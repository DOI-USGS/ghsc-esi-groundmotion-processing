"""Module for the StationTrace class that inherits from obspy's Trace class."""

import inspect

# stdlib imports
import json
import logging
import re

# third party imports
import numpy as np
from obspy.core.trace import Trace
from scipy.integrate import cumulative_trapezoid

# local imports
from gmprocess.core.provenance import TraceProvenance
from gmprocess.io.cosmos.data_structures import BUILDING_TYPES
from gmprocess.io.seedname import get_units_type
from gmprocess.utils.config import get_config
from gmprocess.utils import constants


PROCESS_LEVELS = {
    "V0": "raw counts",
    "V1": "uncorrected physical units",
    "V2": "corrected physical units",
    "V3": "derived time series",
}

REV_PROCESS_LEVELS = {
    "raw counts": "V0",
    "uncorrected physical units": "V1",
    "corrected physical units": "V2",
    "derived time series": "V3",
}

LENGTH_CONVERSIONS = {"nm": 1e9, "um": 1e6, "mm": 1e3, "cm": 1e2, "m": 1}

# when checking to see if a channel is vertical,
# 90 - abs(dip) must be less than or equal to this value
# (i.e., dip must ne close to )
MAX_DIP_OFFSET = 0.1

# NOTE: if required is True then this means that the value must be
# filled in with a value that does NOT match the default.
STANDARD_KEYS = {
    "source_file": {"type": str, "required": False, "default": ""},
    "source": {"type": str, "required": True, "default": ""},
    "horizontal_orientation": {"type": float, "required": False, "default": np.nan},
    "vertical_orientation": {"type": float, "required": False, "default": np.nan},
    "station_name": {"type": str, "required": False, "default": ""},
    "instrument_period": {"type": float, "required": False, "default": np.nan},
    "instrument_damping": {"type": float, "required": False, "default": np.nan},
    "process_time": {"type": str, "required": False, "default": ""},
    "process_level": {
        "type": str,
        "required": True,
        "default": list(PROCESS_LEVELS.values()),
    },
    "sensor_serial_number": {"type": str, "required": False, "default": ""},
    "instrument": {"type": str, "required": False, "default": ""},
    "structure_type": {"type": str, "required": False, "default": ""},
    "structure_cosmos_code": {"type": int, "required": False, "default": 999},
    "corner_frequency": {"type": float, "required": False, "default": np.nan},
    "units": {"type": str, "required": True, "default": ""},
    "units_type": {"type": str, "required": True, "default": ""},
    "source_format": {"type": str, "required": True, "default": ""},
    "instrument_sensitivity": {
        "type": float,
        "required": False,
        "default": np.nan,
    },
    "volts_to_counts": {
        "type": float,
        "required": False,
        "default": np.nan,
    },
    "comments": {"type": str, "required": False, "default": ""},
}

INT_TYPES = [
    np.dtype("int8"),
    np.dtype("int16"),
    np.dtype("int32"),
    np.dtype("int64"),
    np.dtype("uint8"),
    np.dtype("uint16"),
    np.dtype("uint32"),
    np.dtype("uint64"),
]

FLOAT_TYPES = [np.dtype("float32"), np.dtype("float64")]


class StationTrace(Trace):
    """Subclass of Obspy Trace object which holds more metadata.

    ObsPy provides a Trace object that serves as a container for waveform data
    from a single channel, as well as some basic metadata about the waveform
    start/end times, number of points, sampling rate/interval, and
    network/station/channel/location information.

    gmprocess subclasses the Trace object with a StationTrace object, which
    provides the following additional features:

        - Validation that length of data matches the number of points in the
          metadata.
        - Validation that required values are set in metadata.
        - A `fail` method which can be used by processing routines to mark when
          processing of the StationTrace has failed some sort of check (signal
          to noise ratio, etc.)
        - A `free_field` property which can be used to query the object to
          ensure that its data comes from a free-field sensor. Note: this is
          not always known reliably, and different people have have different
          definitions of the term free_field. When possible, we define a
          mapping between location code and the free_field property. For
          example, see the LOCATION_CODES variable core.py in
          `gmprocess.io.fdsn`.
        - Methods (e.g., `get_provenance`, `set_provenance`) for tracking
          processing steps that have been performed. These are aligned with the
          SEIS-PROV standard for processing provenance, described here:
          http://seismicdata.github.io/SEIS-PROV/_generated_details.html#activities
        - Methods (e.g., `get_parameter` and `set_parameter`) for tracking of
          arbitrary metadata in the form of a dictionary as trace property
          (self.parameters).
    """

    def __init__(self, data=np.array([]), header=None, inventory=None, config=None):
        """Construct a StationTrace instance.

        Args:
            data (ndarray):
                numpy array of points.
            header (dict-like):
                Dictionary of metadata (see trace.stats docs).
            inventory (Inventory):
                Obspy Inventory object.
            config (dict):
                Dictionary containing configuration.
                If None, retrieve global config.
        """
        prov_response = None
        if config is None:
            config = get_config()
        if inventory is None and header is None:
            raise ValueError(
                "Cannot create StationTrace without header info or Inventory"
            )
        elif inventory is not None and header is not None:
            # End up here if the format was read in with ObsPy and an
            # inventory was able to be constructed (e.g., miniseed+StationXML)
            try:
                seed_id = (
                    f"{header['network']}.{header['station']}.{header['location']}."
                    f"{header['channel']}"
                )
                start_time = header["starttime"]
                response, standard, coords, format_specific = _stats_from_inventory(
                    data, inventory, seed_id, start_time
                )
                header["response"] = response
                header["coordinates"] = coords
                header["standard"] = standard
                header["format_specific"] = format_specific
            except BaseException as err:
                raise ValueError(
                    "Failed to construct required metadata from inventory "
                    "and input header data with exception: %s.",
                    err,
                )
        elif inventory is None and header is not None and "standard" not in header:
            # End up here for ObsPy without an inventory (e.g., SAC).
            # This assumes that all of our readers include the "standard" key
            # in the header and that ObsPy one's do not.

            # NOTE: we are assuming that an ObsPy file that does NOT have an
            # inventory has been converted to cm/s^2 via the configurable
            # conversion factor in the config file.
            prov_response = {"input_units": "counts", "output_units": "cm/s^2"}
            try:
                (response, standard, coords, format_specific) = _stats_from_header(
                    header, config
                )
                header["response"] = response
                header["coordinates"] = coords
                header["standard"] = standard
                header["format_specific"] = format_specific
            except BaseException:
                raise ValueError(
                    "Failed to construct required metadata from header data."
                )

        # Sometimes the channel names do not indicate which one is the
        # Z channel. If we have vertical_orientation information, then
        # let's get that and change the vertical channel to end in Z
        # as long as the channel name does not include the direction (E, N, Z).
        # Some inventory files mistakenly include a vertical orientation for horizontal channels.
        #     NOTE: `vertical_orientation` here is defined as the angle
        #           from horizontal (aka, dip), not inclination.
        if not np.isnan(header["standard"]["vertical_orientation"]):
            delta = np.abs(np.abs(header["standard"]["vertical_orientation"]) - 90.0)
            is_horizcomp = header["channel"][-1] in ["E", "N"]
            is_vertcomp = header["channel"][-1] in ["Z"]
            if delta < MAX_DIP_OFFSET:
                trace_id = f"{header['network']}.{header['station']}.{header['location']}.{header['channel']}"
                if is_vertcomp:
                    pass
                elif is_horizcomp:
                    logging.warning(
                        "Found vertical orientation in trace %s, which seems to be a horizontal component. Assuming vertical orientation is incorrect.",
                        trace_id,
                    )
                else:
                    header["channel"] = header["channel"][0:-1] + "Z"
                    logging.warning(
                        "Found vertical orientation in trace %s. Component direction is unknown from channel name, so renaming channel to vertical component 'Z'.",
                        trace_id,
                    )

        super(StationTrace, self).__init__(data=data, header=header)
        self.provenance = TraceProvenance(self.stats)
        if prov_response is not None:
            self.set_provenance("remove_response", prov_response)
        self.parameters = {}
        self.parameters["warnings"] = []
        self.cached = {}
        self.validate()

    @property
    def free_field(self):
        """Is this station a free-field station?

        Returns:
            bool: True if a free-field sensor, False if not.
        """
        stype = self.stats.standard["structure_type"]
        non_free = [
            "building",
            "bridge",
            "dam",
            "borehole",
            "hole",
            "crest",
            "toe",
            "foundation",
            "body",
            "roof",
            "floor",
        ]
        for ftype in non_free:
            if re.search(ftype, stype.lower()) is not None:
                return False

        return True

    def fail(self, reason):
        """Note that a check on this StationTrace failed for a given reason.

        This method will set the parameter "failure", and store the reason
        provided, plus the name of the calling function.

        Args:
            reason (str):
                Reason given for failure.

        """
        if self.has_parameter("review"):
            review_dict = self.get_parameter("review")
            if review_dict["accepted"]:
                return
        istack = inspect.stack()
        calling_module = istack[1][3]
        self.set_parameter("failure", {"module": calling_module, "reason": reason})
        trace_id = f"{self.id}"
        logging.info(f"Failure: {calling_module} - {trace_id} - {reason}")

    def warning(self, reason):
        """Add a warning regarding the processing of this trace..

        This method will set the parameter "warnings", which is a list of dictionaries
        in which each dictionary gives the reason for the warning and the name of the
        calling function.

        Args:
            reason (str):
                Reason given for warning.

        """
        previous_warngins = self.get_parameter("warnings")
        istack = inspect.stack()
        calling_module = istack[1][3]
        previous_warngins.append({"module": calling_module, "reason": reason})
        self.set_parameter("warnings", previous_warngins)
        trace_id = f"{self.id}"
        logging.info(f"Warning: {calling_module} - {trace_id} - {reason}")

    @property
    def passed(self):
        """Has this trace passed checks?"""
        return not self.has_parameter("failure")

    @property
    def is_horizontal(self):
        return "z" not in self.stats.channel.lower()

    def validate(self):
        """Ensure that all required metadata fields have been set.

        Raises:
            KeyError:
                - When standard dictionary is missing required fields
                - When standard values are of the wrong type
                - When required values are set to a default.
            ValueError:
                - When number of points in header does not match data length.
        """
        # here's something we thought obspy would do...
        # verify that npts matches length of data
        if self.stats.npts != len(self.data):
            raise ValueError(
                "Number of points in header does not match the number of "
                "points in the data."
            )

        # set the cosmos structure code from the structure type field, if possible
        if "structure_cosmos_code" not in self.stats.standard:
            inverse_btypes = {v: k for k, v in BUILDING_TYPES.items()}
            if self.stats.standard.structure_type == "":
                self.stats.standard["structure_cosmos_code"] = 999
            elif self.stats.standard.structure_type in inverse_btypes:
                self.stats.standard["structure_cosmos_code"] = inverse_btypes[
                    self.stats.standard.structure_type
                ]
            else:
                self.stats.standard["structure_cosmos_code"] = 999

        if "remove_response" not in self.provenance.ids:
            self.stats.standard.units = "raw counts"
            self.stats.standard.units_type = get_units_type(self.stats.channel)

        # are all of the defined standard keys in the standard dictionary?
        req_keys = set(STANDARD_KEYS.keys())
        std_keys = set(list(self.stats.standard.keys()))
        if not req_keys <= std_keys:
            missing = str(req_keys - std_keys)
            raise KeyError(
                f'Missing standard values in StationTrace header: "{missing}"'
            )
        type_errors = []
        required_errors = []
        for key in req_keys:
            keydict = STANDARD_KEYS[key]
            value = self.stats.standard[key]
            required = keydict["required"]
            vtype = keydict["type"]
            default = keydict["default"]
            if not isinstance(value, vtype):
                type_errors.append(key)
            if required:
                if isinstance(default, list):
                    if value not in default:
                        required_errors.append(key)
                if value == default:
                    required_errors.append(key)

        type_error_msg = ""
        if type_errors:
            fmt = 'The following standard keys have the wrong type: "%s"'
            tpl = ",".join(type_errors)
            type_error_msg = fmt % tpl

        required_error_msg = ""
        if required_errors:
            fmt = 'The following standard keys are required: "%s"'
            tpl = ",".join(required_errors)
            required_error_msg = fmt % tpl

        error_msg = type_error_msg + "\n" + required_error_msg
        if error_msg.strip():
            raise KeyError(error_msg)

    def differentiate(self, frequency=True):
        input_units = self.stats.standard.units
        if "/s^2" in input_units:
            output_units = input_units.replace("/s^2", "/s^3")
        elif "/s/s" in input_units:
            output_units = input_units.replace("/s/s", "/s/s/s")
        elif "/s" in input_units:
            output_units = input_units.replace("/s", "/s/s")
        else:
            output_units = input_units + "/s"
        if frequency:
            method = "frequency"
            spec_y = np.fft.rfft(self.data, len(self.data))
            freq_y = np.fft.rfftfreq(len(self.data), d=self.stats.delta)
            spec_dy = spec_y * (2j * np.pi * freq_y)
            self.data = np.fft.irfft(spec_dy)
        else:
            method = "gradient"
            self = super().differentiate(method=method)
        self.set_provenance(
            "differentiate",
            {
                "differentiation_method": method,
                "input_units": self.stats.standard.units,
                "output_units": output_units,
            },
        )

        return self

    def zero_pad(self, length):
        """Zero pad trace and add entry to provenance.

        Zero pads are added at the beginning and end of the trace, EACH of which has
        duration of `length` (in sec).

        Args:
            length (float):
                The length (in sec) to padd with zeros before and after the trace.
        """
        old_start_time = self.stats.starttime
        old_end_time = self.stats.endtime
        start_time = self.stats.starttime - length
        end_time = self.stats.endtime + length
        fill_value = np.array(0, dtype=self.data.dtype)
        self.trim(
            starttime=start_time,
            endtime=end_time,
            pad=True,
            fill_value=fill_value,
            suppress_provenance=True,
        )

        self.set_provenance(
            "pad",
            {
                "fill_value": 0.0,
                "new_start_time": start_time,
                "new_end_time": end_time,
                "old_start_time": old_start_time,
                "old_end_time": old_end_time,
            },
        )
        return self

    def strip_zero_pad(self):
        """Remove zero pads from trace."""

        pad_prov = self.get_provenance("pad")
        if len(pad_prov) > 1:
            raise ValueError("More than one 'pad' entry in provenance.")
        start_time = pad_prov[0]["prov_attributes"].get("old_start_time")
        end_time = pad_prov[0]["prov_attributes"].get("old_end_time")
        self.trim(starttime=start_time, endtime=end_time)

        return self

    def taper(self, max_percentage, type="hann", max_length=None, side="both"):
        """Taper trace and add entry to provenance.

        This just overrides the ObsPy Trace method to append to the provenance for
        tracking this operation.

        Args:
            max_percentage (float):
                 Decimal percentage of taper at one end (ranging from 0. to 0.5).
            type (str):
                Type of taper to use for detrending.
            max_length (float):
                Length of taper at one end in seconds.
            side (str):
                Specify if both sides should be tapered (default, “both”) or if only the
                left half (“left”) or right half (“right”) should be tapered.
        """

        self.set_provenance(
            "taper",
            {
                "max_percentage": max_percentage,
                "type": type,
                "side": side,
                "max_length": max_length,
            },
        )
        return super().taper(
            max_percentage=max_percentage,
            type=type,
            side=side,
            max_length=max_length,
        )

    def detrend(self, type="simple"):
        """Detrend trace and add entry to provenance.

        This just overrides the ObsPy Trace method to append to the provenance for
        tracking this operation.

        Args:
            type (str):
                 Method to use for detrending.
        """
        prov_dict = {"detrending_method": type}
        if type in ["constant", "demean"]:
            prov_dict["value"] = np.mean(self.data)
            self.data = np.array(self.data, dtype=float) - prov_dict["value"]
        else:
            super().detrend(type=type)
        self.set_provenance("detrend", prov_dict)
        return self

    def trim(
        self,
        starttime=None,
        endtime=None,
        pad=False,
        nearest_sample=True,
        fill_value=None,
        suppress_provenance=False,
    ):
        """Trim trace and add entry to provenance.

        This just overrides the ObsPy Trace method to append to the provenance for
        tracking this operation.

        Args:
            starttime (UTCDateTime):
                Start time.
            endtime (UTCDateTime):
                End time.
            pad (bool):
                Trim at time points outside the time frame of the original trace?
            nearest_sample (bool):
                See obspy docs.
            fill_value (int, float):
                Fill value for gaps.
            suppress_provenance (bool):
                Do not put a provenance entry. Useful because we need a custom
                provenance entry for zero padding, which calls this method.
        """
        if not suppress_provenance:
            prov_dict = {"new_start_time": starttime, "new_end_time": endtime}
            if pad:
                prov_dict["fill_value"] = fill_value
            self.set_provenance("cut", prov_dict)
        return super().trim(starttime, endtime, pad, nearest_sample, fill_value)

    def integrate(
        self,
        frequency=True,
        initial=0.0,
        demean=False,
        taper=False,
        taper_width=0.05,
        taper_type="hann",
        taper_side="both",
    ):
        """Integrate a StationTrace with respect to either frequency or time.

        Args:
            frequency (bool):
                Determine if we're integrating in frequency domain.
                If not, integrate in time domain.
            initial (float):
                Define initial value returned in result.
            demean (bool):
                Remove mean from array before integrating.
            taper (bool):
                Apply a taper.
            taper_width (float):
                Taper width.
            taper_type (float):
                Taper type.
            taper_side (float):
                Taper side.

        Returns:
            StationTrace: Input StationTrace is integrated and returned.
        """

        if demean:
            self.detrend(type="demean")

        if taper:
            self.taper(max_percentage=taper_width, type=taper_type, side=taper_side)

        if frequency:
            # integrating in frequency domain
            method = "frequency domain"
            # take discrete FFT and get the discretized frequencies
            npts = len(self.data)
            spec_in = np.fft.rfft(self.data, n=npts)
            freq = np.fft.rfftfreq(npts, self.stats.delta)

            # Replace frequency of zero with 1.0 to avoid division by zero. This will
            # cause the DC (mean) to be unchanged by the integration/division.
            freq[0] = 1.0
            spec_out = spec_in / 2.0j / np.pi / freq

            # calculate inverse FFT back to time domain
            integral_result = np.fft.irfft(spec_out, n=npts)

            # Apply initial condition
            shift = integral_result[0] - initial

            self.data = integral_result - shift

        else:
            # integrating in time domain
            method = "time domain"
            integral_result = cumulative_trapezoid(
                self.data, dx=self.stats.delta, initial=initial
            )
            self.data = integral_result

        input_units = self.stats.standard.units
        if "/s^2" in input_units:
            output_units = input_units.replace("/s^2", "/s")
        elif "/s/s" in input_units:
            output_units = input_units.replace("/s/s", "/s")
        elif "/s" in input_units:
            output_units = input_units.replace("/s", "")
        else:
            output_units = input_units + "*s"
        self.set_provenance(
            "integrate",
            {
                "integration_method": method,
                "input_units": self.stats.standard.units,
                "output_units": output_units,
            },
        )

        return self

    def filter(
        self,
        type="highpass",
        freq=0.05,
        freqmin=0.1,
        freqmax=20,
        corners=5.0,
        zerophase=False,
        config=None,
        frequency_domain=True,
    ):
        """Overwrite parent function to allow for configuration options.

        Args:
            type (str):
                What type of filter? "highpass" or "lowpass" or "bandpass" or
                "bandstop".
            freq (float):
                Corner frequency (Hz) used for "highpass" or "lowpass".
            freqmin (float):
                Low corner frequency (Hz) used for "bandpass" or "bandstop".
            freqmax (float):
                High corner frequency (Hz) used for "bandpass" or "bandstop".
            corners (float):
                Number of poles.
            zerophase (bool):
                Zero phase filter?
            config (dict):
                Configuration options.
            frequency_domain (bool):
                Apply filter in frequency domain?
        """
        if zerophase:
            number_of_passes = 2
        else:
            number_of_passes = 1
        if type == "lowpass":
            if not frequency_domain:
                self.set_provenance(
                    "lowpass_filter",
                    {
                        "filter_type": "Butterworth ObsPy",
                        "filter_order": corners,
                        "number_of_passes": number_of_passes,
                        "corner_frequency": freq,
                    },
                )
                return super().filter(
                    type=type,
                    freq=freq,
                    corners=corners,
                    zerophase=zerophase,
                )

            else:
                if zerophase:
                    logging.warning(
                        "Filter is only applied once in frequency domain, "
                        "even if number of passes is 2"
                    )

                self.__compute_fft()
                filter = np.sqrt(1.0 + (self.signal_freq / freq) ** (2.0 * corners))
                self.__apply_filter(filter)

                self.set_provenance(
                    "lowpass_filter",
                    {
                        "filter_type": "Butterworth gmprocess",
                        "filter_order": corners,
                        "number_of_passes": number_of_passes,
                        "corner_frequency": freq,
                    },
                )

        elif type == "highpass":
            if not frequency_domain:
                self.set_provenance(
                    "highpass_filter",
                    {
                        "filter_type": "Butterworth ObsPy",
                        "filter_order": corners,
                        "number_of_passes": number_of_passes,
                        "corner_frequency": freq,
                    },
                )
                return super().filter(
                    type,
                    freq=freq,
                    corners=corners,
                    zerophase=zerophase,
                )

            else:
                if zerophase:
                    logging.warning(
                        "Filter is only applied once in frequency domain, "
                        "even if number of passes is 2"
                    )

                self.__compute_fft()
                filter = np.sqrt(1.0 + (freq / self.signal_freq) ** (2.0 * corners))
                self.__apply_filter(filter)

                self.set_provenance(
                    "highpass_filter",
                    {
                        "filter_type": "Butterworth gmprocess",
                        "filter_order": corners,
                        "number_of_passes": number_of_passes,
                        "corner_frequency": freq,
                    },
                )

        elif type == "bandpass":
            if not frequency_domain:
                self.set_provenance(
                    "bandpass_filter",
                    {
                        "filter_type": "Butterworth ObsPy",
                        "filter_order": corners,
                        "number_of_passes": number_of_passes,
                        "lower_corner_frequency": freqmin,
                        "upper_corner_frequency": freqmax,
                    },
                )
                return super().filter(
                    type,
                    freqmin=freqmin,
                    freqmax=freqmax,
                    corners=corners,
                    zerophase=zerophase,
                )

            else:
                if zerophase:
                    logging.warning(
                        "Filter is only applied once in frequency domain, "
                        "even if number of passes is 2"
                    )
                self.__compute_fft()
                filter = np.sqrt(1.0 + (freqmin / self.signal_freq) ** (2.0 * corners))
                filter *= np.sqrt(1.0 + (self.signal_freq / freqmax) ** (2.0 * corners))
                self.__apply_filter(filter)

                self.set_provenance(
                    "bandpass_filter",
                    {
                        "filter_type": "Butterworth gmrocess",
                        "filter_order": corners,
                        "number_of_passes": number_of_passes,
                        "lower_corner_frequency": freqmin,
                        "upper_corner_frequency": freqmax,
                    },
                )
        elif type == "bandstop":
            if not frequency_domain:
                self.set_provenance(
                    "bandstop_filter",
                    {
                        "filter_type": "Butterworth ObsPy",
                        "filter_order": corners,
                        "number_of_passes": number_of_passes,
                        "lower_corner_frequency": freqmin,
                        "upper_corner_frequency": freqmax,
                    },
                )
                return super().filter(
                    type,
                    freqmin=freqmin,
                    freqmax=freqmax,
                    corners=corners,
                    zerophase=zerophase,
                )

            else:
                if zerophase:
                    logging.warning(
                        "Filter is only applied once in frequency domain, "
                        "even if number of passes is 2"
                    )

                self.__compute_fft()
                filter = np.sqrt(1.0 + (freq / self.signal_freq) ** (2.0 * corners))
                filter *= np.sqrt(1.0 + (self.signal_freq / freq) ** (2.0 * corners))
                filter = 1 - filter
                self.__apply_filter(filter)

                self.set_provenance(
                    "bandstop_filter",
                    {
                        "filter_type": "Butterworth gmprocess",
                        "filter_order": corners,
                        "number_of_passes": number_of_passes,
                        "lower_corner_frequency": freqmin,
                        "upper_corner_frequency": freqmax,
                    },
                )
        else:
            raise TypeError(f"Unsupported filter type: {type}")

        return self

    def get_provenance(self, prov_id):
        """Get seis-prov compatible attributes whose id matches prov_id.

        See http://seismicdata.github.io/SEIS-PROV/_generated_details.html

        Args:
            prov_id (str):
                Provenance property "prov:id", e.g., "detrend".

        Returns:
            list: Sequence of prov_attribute dictionaries.
        """
        return self.provenance.select(prov_id)

    def set_provenance(self, prov_id, prov_attributes):
        """Update a trace's provenance information.

        Args:
            trace (obspy.core.trace.Trace):
                Trace of strong motion dataself.
            prov_id (str):
                Activity prov:id (see URL above).
            prov_attributes (dict or list):
                Activity attributes for the given key.
        """
        provdict = {"prov_id": prov_id, "prov_attributes": prov_attributes}
        self.provenance.append(provdict)
        if "output_units" in prov_attributes.keys():
            self.stats.standard.units = prov_attributes["output_units"]
            try:
                self.stats.standard.units_type = constants.REVERSE_UNITS[
                    prov_attributes["output_units"]
                ]
            except BaseException:
                self.stats.standard.units_type = "unknown"

    def has_parameter(self, param_id):
        """Check to see if Trace contains a given parameter.

        Args:
            param_id (str): Name of parameter to check.

        Returns:
            bool: True if parameter is set, False if not.
        """
        return param_id in self.parameters

    def set_parameter(self, param_id, param_attributes):
        """Add to the StationTrace's set of arbitrary metadata.

        Args:
            param_id (str):
                Key for parameters dictionary.
            param_attributes (dict or list):
                Parameters for the given key.
        """
        self.parameters[param_id] = param_attributes

    def set_cached(self, name, array_dict):
        """Store a dictionary of arrays in StationTrace.

        Args:
            name (str):
                Name of data dictionary to be stored.
            array_dict (dict):
                Dictionary with:
                    - key array name
                    - value as numpy array
        """
        self.cached[name] = array_dict

    def get_cached(self, name, missing_none=False):
        """Retrieve a dictionary of arrays.

        Args:
            name (str):
                Name of dictionary to retrieve.
            missing_none (bool):
                Return None if key is missing.
        Returns:
            dict: Dictionary of arrays (see setSpectrum).
        """
        if name not in self.cached:
            if missing_none:
                return None
            else:
                raise KeyError(f"{name} not in set of spectra arrays.")
        return self.cached[name]

    def has_cached(self, name):
        """Check if StationTrace has cached attribute."""
        if name not in self.cached:
            return False
        return True

    def get_cached_names(self):
        """Return list of arrays that have been cached.

        Returns:
            list: List of cached arrays in this StationTrace.
        """
        return list(self.cached.keys())

    def get_parameter_keys(self):
        """Get a list of all available parameter keys.

        Returns:
            list: List of available parameter keys.
        """
        return list(self.parameters.keys())

    def get_parameter(self, param_id, missing_none=False):
        """Retrieve some arbitrary metadata.

        Args:
            param_id (str):
                Key for parameters dictionary.
            missing_none (bool):
                Return None if key is missing.

        Returns:
            dict or list:
                Parameters for the given key.
        """
        if param_id not in self.parameters:
            if missing_none:
                return None
            else:
                raise KeyError(f"Parameter {param_id} not found in StationTrace")
        return self.parameters[param_id]

    def __str__(self, id_length=None, indent=0):
        """
        Extends Trace __str__.
        """
        # set fixed id width

        if id_length:
            out = "%%-%ds" % (id_length)
            trace_id = out % self.id
        else:
            trace_id = f"{self.id}"
        out = ""
        # output depending on delta or sampling rate bigger than one
        if self.stats.sampling_rate < 0.1:
            if hasattr(self.stats, "preview") and self.stats.preview:
                out = (
                    out + " | "
                    "%(starttime)s - %(endtime)s | "
                    + "%(delta).1f s, %(npts)d samples [preview]"
                )
            else:
                out = (
                    out + " | "
                    "%(starttime)s - %(endtime)s | " + "%(delta).1f s, %(npts)d samples"
                )
        else:
            if hasattr(self.stats, "preview") and self.stats.preview:
                out = (
                    out + " | "
                    "%(starttime)s - %(endtime)s | "
                    + "%(sampling_rate).1f Hz, %(npts)d samples [preview]"
                )
            else:
                out = (
                    out + " | "
                    "%(starttime)s - %(endtime)s | "
                    + "%(sampling_rate).1f Hz, %(npts)d samples"
                )
        # check for masked array
        if np.ma.count_masked(self.data):
            out += " (masked)"
        if not self.passed:
            out += " (failed)"
        else:
            out += " (passed)"
        ind_str = " " * indent
        return ind_str + trace_id + out % (self.stats)

    def __compute_fft(self):
        self.signal_spec = np.fft.rfft(self.data, n=self.stats.npts)
        self.signal_freq = np.fft.rfftfreq(self.stats.npts, self.stats.delta)
        self.signal_freq[0] = 1.0

    def __apply_filter(self, filter):
        filtered_spec = self.signal_spec / filter
        filtered_spec[0] = 0.0
        self.signal_freq[0] = 0

        # inverse fft to time domain
        filtered_trace = np.fft.irfft(filtered_spec, n=self.stats.npts)
        self.data = filtered_trace


def _stats_from_inventory(data, inventory, seed_id, start_time):
    if len(inventory.source):
        if inventory.sender is not None and inventory.sender != inventory.source:
            source = f"{inventory.source},{inventory.sender}"
        else:
            source = inventory.source

    network_code, station_code, location_code, channel_code = seed_id.split(".")

    selected_inventory = inventory.select(
        network=network_code,
        station=station_code,
        location=location_code,
        channel=channel_code,
        time=start_time,
    )

    station = selected_inventory.networks[0].stations[0]
    channel = station.channels[0]

    coords = {
        "latitude": channel.latitude,
        "longitude": channel.longitude,
        "elevation": channel.elevation,
    }

    standard = {}

    # things we'll never get from an inventory object
    standard["corner_frequency"] = np.nan
    standard["instrument_damping"] = np.nan
    standard["instrument_period"] = np.nan
    standard["structure_type"] = ""
    standard["process_time"] = ""

    if data.dtype in INT_TYPES:
        standard["process_level"] = "raw counts"
    else:
        standard["process_level"] = "uncorrected physical units"

    standard["source"] = source
    standard["source_file"] = ""
    standard["instrument"] = ""
    standard["sensor_serial_number"] = ""
    if channel.sensor is not None:
        standard["instrument"] = (
            f"{channel.sensor.type} {channel.sensor.manufacturer} "
            f"{channel.sensor.model} {channel.sensor.description}"
        )
        if channel.sensor.serial_number is not None:
            standard["sensor_serial_number"] = channel.sensor.serial_number
        else:
            standard["sensor_serial_number"] = ""

    if channel.azimuth is not None:
        standard["horizontal_orientation"] = channel.azimuth
    else:
        standard["horizontal_orientation"] = np.nan

    if channel.dip is not None:
        # Note: vertical orientatin is defined here as angle from horizontal
        standard["vertical_orientation"] = channel.dip
    else:
        standard["vertical_orientation"] = np.nan

    if len(channel.comments):
        comments = " ".join(comment.value for comment in channel.comments)
        standard["comments"] = comments
    else:
        standard["comments"] = ""
    standard["station_name"] = ""
    if station.site.name != "None":
        standard["station_name"] = station.site.name
    # extract the remaining standard info and format_specific info
    # from a JSON string in the station description.

    format_specific = {}
    if station.description is not None and station.description != "None":
        jsonstr = station.description
        try:
            big_dict = json.loads(jsonstr)
            standard.update(big_dict["standard"])
            format_specific = big_dict["format_specific"]
        except json.decoder.JSONDecodeError:
            format_specific["description"] = jsonstr

    if "source_format" not in standard or standard["source_format"] is None:
        standard["source_format"] = "fdsn"

    standard["instrument_sensitivity"] = np.nan
    standard["volts_to_counts"] = np.nan
    response = None
    if channel.response is None:
        return (response, standard, coords, format_specific)
    response = channel.response
    if not hasattr(response, "instrument_sensitivity"):
        return (response, standard, coords, format_specific)

    units = response.instrument_sensitivity.input_units
    if "/" in units:
        num, _ = units.split("/")
        if num.lower() not in LENGTH_CONVERSIONS:
            raise KeyError(f"Sensitivity input units of {units} are not supported.")
        conversion = LENGTH_CONVERSIONS[num.lower()]
        sensitivity = response.instrument_sensitivity.value * conversion
        response.instrument_sensitivity.value = sensitivity
        standard["instrument_sensitivity"] = sensitivity
        # find the volts to counts stage and store that
        if hasattr(response, "response_stages"):
            for stage in response.response_stages:
                if stage.input_units == "V" and stage.output_units == "COUNTS":
                    standard["volts_to_counts"] = stage.stage_gain
                    break
    else:
        standard["instrument_sensitivity"] = response.instrument_sensitivity.value

    return (response, standard, coords, format_specific)


def _stats_from_header(header, config):
    if "_format" in header and header._format.lower() == "sac":
        # The plan is to add separate if blocks to support the different
        # formats as we encounter them here. See the SAC header documentation
        # here:
        # http://ds.iris.edu/files/sac-manual/manual/file_format.html

        # Todo: add support for SAC with PZ file.

        coords = {
            "latitude": header["sac"]["stla"],
            "longitude": header["sac"]["stlo"],
            "elevation": header["sac"]["stel"],
        }
        standard = {}
        standard["corner_frequency"] = np.nan
        standard["instrument_damping"] = np.nan
        standard["instrument_period"] = np.nan
        standard["structure_type"] = ""
        standard["process_time"] = ""
        standard["process_level"] = "uncorrected physical units"
        standard["source"] = config["read"]["sac_source"]
        standard["source_file"] = ""
        standard["instrument"] = ""
        standard["sensor_serial_number"] = ""
        standard["horizontal_orientation"] = float(header["sac"]["cmpaz"])
        # Note: vertical orientatin is defined here as angle from horizontal
        standard["vertical_orientation"] = 90.0 - float(header["sac"]["cmpinc"])
        if "units_type" not in standard or standard["units_type"] == "":
            utype = get_units_type(header["channel"])
            standard["units_type"] = utype
            standard["units"] = constants.UNIT_TYPES[utype]
        standard["comments"] = ""
        standard["station_name"] = ""
        standard["station_name"] = header["station"]
        format_specific = {
            "conversion_factor": float(config["read"]["sac_conversion_factor"])
        }
        standard["source_format"] = header._format
        standard["instrument_sensitivity"] = np.nan
        standard["volts_to_counts"] = np.nan
        response = None
    else:
        raise Exception("Format unsupported without StationXML file.")

    return (response, standard, coords, format_specific)
