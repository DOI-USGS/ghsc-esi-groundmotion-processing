"""Methods for handling instrument response."""

import logging

import numpy as np
from gmprocess.core.stationtrace import PROCESS_LEVELS
from gmprocess.utils import constants
from gmprocess.waveform_processing.processing_step import processing_step
from pint import UnitRegistry

ABBREV_UNITS = {"ACC": "cm/s^2", "VEL": "cm/s", "DISP": "cm"}
OUTPUT = "ACC"

unit_registry = UnitRegistry()

# lower case all input units before checking
STAGE_UNITS = {
    "none.specified": None,
    # linear measures
    "m": unit_registry.meter,
    "cm": unit_registry.centimeter,
    "mm": unit_registry.nanometer,
    "nm": unit_registry.nanometer,
    "v": unit_registry.volt,
    # volts/counts
    "volt": unit_registry.volt,
    "volts": unit_registry.volt,
    "count": unit_registry.count,
    "counts": unit_registry.count,
    # rates
    "m/s": unit_registry.meter / unit_registry.second,
    "cm/s": unit_registry.centimeter / unit_registry.second,
    "mm/s": unit_registry.millimeter / unit_registry.second,
    "nm/s": unit_registry.nanometer / unit_registry.second,
    # accelerations
    "m/s**2": unit_registry.meter / unit_registry.second**2,
    "cm/s**2": unit_registry.centimeter / unit_registry.second**2,
    "mm/s**2": unit_registry.millimeter / unit_registry.second**2,
    "nm/s**2": unit_registry.nanometer / unit_registry.second**2,
    "m/s/s": unit_registry.meter / unit_registry.second**2,
    "cm/s/s": unit_registry.centimeter / unit_registry.second**2,
    "mm/s/s": unit_registry.millimeter / unit_registry.second**2,
    "nm/s/s": unit_registry.nanometer / unit_registry.second**2,
}

# Taper width for tapering velocity before differentiating
TAPER_WIDTH = 0.05


@processing_step
def remove_response(
    st,
    sensitivity_threshold=10.0,
    pre_filt=True,
    f1=0.001,
    f2=0.005,
    f3=None,
    f4=None,
    water_level=60,
    inv=None,
    config=None,
):
    """Perform the instrument response correction.

    If the response information is not already attached to the stream, then an
    inventory object must be provided. If the instrument is a strong-motion
    accelerometer, then tr.remove_sensitivity() will be used. High-gain seismometers
    will use tr.remove_response() with the defined pre-filter and water level.

    If f3 is Null it will be set to 0.9*fn, if f4 is Null it will be set to fn.

    Args:
        st (StationStream):
            Stream of data.
        sensitivity_threshold (float):
            Traces will be failed if the overall reported sensitivity differs by more
            than this threshold (units are percent) when compared to the sensitivty as
            computed by combining the reported gains of each response stage.
        pre_filt (bool):
            Apply a bandpass filter in frequency domain to the data before
            deconvolution?
        f1 (float):
            Frequency 1 for pre-filter.
        f2 (float):
            Frequency 2 for pre-filter.
        f3 (float):
            Frequency 3 for pre-filter.
        f4 (float):
            Frequency 4 for pre-filter.
        water_level (float):
            Water level for deconvolution.
        inv (obspy.core.inventory.inventory):
            Obspy inventory object containing response information.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: With instrument response correction applied.
    """
    resp = RemoveResponse(
        st, sensitivity_threshold, pre_filt, f1, f2, f3, f4, water_level, inv, config
    )
    return resp.stream


class RemoveResponse(object):
    """Class for removing instrument response."""

    def __init__(
        self,
        st,
        sensitivity_threshold=10.0,
        pre_filt=True,
        f1=0.001,
        f2=0.005,
        f3=None,
        f4=None,
        water_level=60,
        inv=None,
        config=None,
    ):
        self.unit_registry = UnitRegistry()
        self.stream = st
        self.sensitivity_threshold = sensitivity_threshold
        self.pre_filt = pre_filt
        self.f1 = f1
        self.f2 = f2
        self.f3 = f3
        self.f4 = f4
        self.water_level = water_level
        self.inv = inv
        if self.inv is None:
            self.inv = self.stream.get_inventory()
        self.config = config
        for self.trace in self.stream:
            if "remove_response" in self.trace.provenance.ids:
                continue
            self._set_pre_filt()
            self._set_poles_and_zeros()
            self._remove_response_selector()

    def _set_pre_filt(self):
        self.f_n = 0.5 / self.trace.stats.delta
        if self.f3 is None:
            self.f3 = 0.9 * self.f_n
        if self.f4 is None:
            self.f4 = self.f_n
        if self.pre_filt:
            self.pre_filt = (self.f1, self.f2, self.f3, self.f4)
        else:
            self.pre_filt = None

    def _set_poles_and_zeros(self):
        self.resp = self.inv.get_response(self.trace.id, self.trace.stats.starttime)
        try:
            self.paz = self.resp.get_paz()
            self.has_paz = not (len(self.paz.poles) == 0 and len(self.paz.zeros) == 0)
        except Exception:
            self.paz = None
            self.has_paz = False

    def _remove_response_selector(self):
        self.instrument_code = self.trace.stats.channel[1]
        if self.instrument_code not in "NH":
            reason = (
                "This instrument type is not supported. The instrument code must be "
                "either H (high gain seismometer) or N (accelerometer)."
            )
            self.trace.fail(reason)
            return

        if (self.instrument_code == "H") and (not self.has_paz):
            reason = (
                "Instrument is a seismometer and does not have poles and zeros for "
                "response."
            )
            self.trace.fail(reason)
            return

        if self.has_paz:
            try:
                self._remove_response()
            except BaseException as exc:
                logging.info(
                    "Encountered an error when in remove_response: %s. Now using "
                    "remove_sensitivity instead.",
                    str(exc),
                )
                self._remove_sensitivity()
        else:
            self._remove_sensitivity()

    def _remove_response(self):
        try:
            # Note: rater than set OUTPUT to 'ACC' for seismometers, we are are setting
            # it to 'VEL" and then differentiating.
            if self.instrument_code == "H":
                output_units = "VEL"
            else:
                output_units = "ACC"
            # ** add check on gain/overall sensitivity here.
            self._check_sensitivity()
            if self.sensitivity_check_passed:
                self.trace.remove_response(
                    inventory=self.inv,
                    output=output_units,
                    water_level=self.water_level,
                    pre_filt=self.pre_filt,
                    zero_mean=True,
                    taper=False,
                )
                self.trace.set_provenance(
                    "remove_response",
                    {
                        "method": "remove_response",
                        "input_units": "counts",
                        "output_units": ABBREV_UNITS[output_units],
                        "water_level": self.water_level,
                        "pre_filt_freqs": str(self.pre_filt),
                    },
                )
            else:
                if self.instrument_code == "N":
                    self._remove_sensitivity()
                else:
                    reason = "Stage gains are inconsistent with overall sensitivity."
                    self.trace.fail(reason)

            # Differentiate if this is a seismometer
            if self.instrument_code == "H":
                diff_conf = self.config["differentiation"]
                self.trace.taper(TAPER_WIDTH)
                self.trace.differentiate(frequency=diff_conf["frequency"])

            self.trace.data *= constants.M_TO_CM  # Convert from m to cm
            self.trace.stats.standard.units = ABBREV_UNITS[OUTPUT]
            self.trace.stats.standard.units_type = OUTPUT.lower()
            self.trace.stats.standard.process_level = PROCESS_LEVELS["V1"]
        except BaseException as e:
            raise e
            reason = (
                "Encountered an error when attempting to remove instrument response: "
                f"{str(e)}"
            )
            self.trace.fail(reason)
            return

        # Response removal can also result in NaN values due to bad metadata, so check
        # that data contains no NaN or inf values
        if not np.isfinite(self.trace.data).all():
            reason = "Non-finite values encountered after removing instrument response."
            self.trace.fail(reason)

    def _remove_sensitivity(self):
        self.trace.remove_sensitivity(inventory=self.inv)
        self.trace.data *= constants.M_TO_CM  # Convert from m to cm
        self.trace.set_provenance(
            "remove_response",
            {
                "method": "remove_sensitivity",
                "input_units": "counts",
                "output_units": ABBREV_UNITS[OUTPUT],
            },
        )
        self.trace.stats.standard.units = ABBREV_UNITS[OUTPUT]
        self.trace.stats.standard.units_type = OUTPUT.lower()
        self.trace.stats.standard.process_level = PROCESS_LEVELS["V1"]

    def _check_sensitivity(self):
        network = self.trace.stats.network
        station = self.trace.stats.station
        channel = self.trace.stats.channel
        inventory = self.inv.select(
            network=network,
            station=station,
            channel=channel,
        )
        response = inventory[0][0][0].response
        overall_sensitivity = response.instrument_sensitivity.value
        sensivity_input_units = STAGE_UNITS.get(
            response.instrument_sensitivity.input_units.lower(), None
        )
        sensivity_output_units = STAGE_UNITS.get(
            response.instrument_sensitivity.output_units.lower(), None
        )
        if sensivity_input_units is None or sensivity_output_units is None:
            logging.warning(
                f"{network}.{station}.{channel} instrument sensitivity is missing units"
            )
            overall_sensitivity *= unit_registry.dimensionless
        else:
            overall_sensitivity *= sensivity_input_units / sensivity_output_units
        stages = response.response_stages
        combined_stage_sensitivity = 1.0 * unit_registry.dimensionless
        for stage in stages:
            stagenum = stage.stage_sequence_number
            input_units = STAGE_UNITS.get(
                stage.input_units.lower(), unit_registry.dimensionless
            )
            output_units = STAGE_UNITS.get(
                stage.output_units.lower(), unit_registry.dimensionless
            )
            if (
                input_units == unit_registry.dimensionless
                or output_units == unit_registry.dimensionless
            ):
                logging.warning(
                    f"{network}.{station}.{channel} Stage {stagenum} missing units"
                )

            combined_stage_sensitivity *= stage.stage_gain * (
                input_units / output_units
            )
        # Percent difference relative to mean value
        pct_diff = (
            200.0
            * np.abs(
                overall_sensitivity.magnitude - combined_stage_sensitivity.magnitude
            )
            / (overall_sensitivity.magnitude + combined_stage_sensitivity.magnitude)
        )
        if pct_diff > self.sensitivity_threshold:
            self.sensitivity_check_passed = False
        else:
            self.sensitivity_check_passed = True
        self.units_check_passed = True
        dimensionless = (
            overall_sensitivity.dimensionless
            or combined_stage_sensitivity.dimensionless
        )
        if (
            overall_sensitivity.units != combined_stage_sensitivity.units
            or dimensionless
        ):
            self.units_check_passed = False
