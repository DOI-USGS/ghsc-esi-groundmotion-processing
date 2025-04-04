"""Module for the StationStream classs."""

# stdlib imports
import logging

# third party imports
import numpy as np
from gmprocess.utils import constants

# local imports
from gmprocess.utils.config import get_config
from obspy.core.inventory import (
    Channel,
    Comment,
    Equipment,
    InstrumentSensitivity,
    Inventory,
    Network,
    Response,
    Site,
    Station,
)
from obspy.core.stream import Stream
from obspy.core.utcdatetime import UTCDateTime

from .stationtrace import StationTrace

# Number of samples for Landzos interpolation.
N_LANCZOS = 20

UNUSED_STANDARD_PARAMS = [
    "instrument_period",
    "instrument_damping",
    "process_time",
    "process_level",
    "structure_type",
    "corner_frequency",
    "source_file",
    "source_format",
]

TIME_TOL = 1e-5


class StationStream(Stream):
    """The gmprocess subclass of ObsPy's Stream object.

    ObsPy provides a Stream object that serves as a container for zero-to-many
    Trace objects, and gmprocess subclasses the Stream object with the
    StationStream object, which contains StationTrace objects. It also provides
    facilities for extracting ObsPy inventory data structures, and provenance
    from the contained StationTrace objects.

    The StationStream class is meant for grouping Traces from the same
    "station". In practice, what this really means is usually all of the
    channels from one instrument, with the same start and end times. Thus,
    the StationStream object has a get_id method, which returns a string that
    consists of the network code, station code, and the first two characters
    of the channel code, since these should all be applicable to all traces in
    the StationStream object.
    """

    def __init__(self, traces=None, inventory=None, config=None):
        self.traces = []
        self.config = config
        self.parameters = {}
        if self.config is None:
            self.config = get_config()
        self.set_stream_param(
            "any_trace_failures", self.config["check_stream"]["any_trace_failures"]
        )

        if len(traces):
            # sometimes traces have different start/end times
            # let's get the minimum bounding times here
            # and trim the trace before we add it to the stream.
            starts = [trace.stats.starttime for trace in traces]
            ends = [trace.stats.endtime for trace in traces]
            sts = [s.timestamp for s in starts]
            ets = [e.timestamp for e in ends]

            # Do we need to try to fix the start/end times?
            times_match = True
            if len(sts) > 1:
                sdiff = np.abs(np.diff(sts)).max()
                ediff = np.abs(np.diff(ets)).max()
                times_match = (sdiff < TIME_TOL) and (ediff < TIME_TOL)
            if not times_match:
                newstart = max(starts)
                newend = min(ends)
                if newstart >= newend:
                    for trace in traces:
                        trace.fail(
                            "Trimming start/end times across traces for this stream "
                            "resulting in a start time after the end time."
                        )
                        self.append(trace)
                else:
                    # First try to simply cut, the most minimally invasive
                    # option
                    for trace in traces:
                        if inventory is None:
                            if not isinstance(trace, StationTrace):
                                raise ValueError(
                                    "Input Traces to StationStream must be of subtype "
                                    "StationTrace unless an inventory is also provided."
                                )
                        else:
                            if not isinstance(trace, StationTrace):
                                trace = StationTrace(
                                    data=trace.data,
                                    header=trace.stats,
                                    inventory=inventory,
                                )

                        # Apply the new start/end times
                        trace = trace.slice(starttime=newstart, endtime=newend)
                        trace.set_provenance(
                            "cut", {"new_start_time": newstart, "new_end_time": newend}
                        )

                        self.append(trace)

                    # Did that work?
                    starts = [trace.stats.starttime for trace in self.traces]
                    sts = [s.timestamp for s in starts]
                    ends = [trace.stats.endtime for trace in self.traces]
                    ets = [e.timestamp for e in ends]
                    deltas = [trace.stats.delta for trace in self.traces]
                    new_delta = min(deltas)
                    newstart = max(starts)
                    newend = min(ends)
                    new_duration = newend - newstart
                    new_npts = int(new_duration / new_delta + 1)
                    success = len(set(sts)) == 1 and len(set(ets)) == 1

                    # If not, resample
                    if not success:
                        try:
                            for tr in self.traces:
                                tr.interpolate(
                                    sampling_rate=1 / new_delta,
                                    method="lanczos",
                                    starttime=newstart,
                                    npts=new_npts,
                                    a=N_LANCZOS,
                                )
                                tr.set_provenance(
                                    "interpolate",
                                    {
                                        "interpolation_method": "lanczos",
                                        "new_number_of_samples": new_npts,
                                        "new_start_time": newstart,
                                        "a": N_LANCZOS,
                                    },
                                )
                        except BaseException:
                            for tr in self.traces:
                                tr.fail("Traces within stream are misaligned.")
            else:
                # start/end times may be different but within tolerance
                # to prevent further issues downstream, setting these
                # to be all the same.
                start_time = traces[0].stats.starttime
                for trace in traces:
                    trace.stats.starttime = start_time
                    if inventory is None:
                        if not isinstance(trace, StationTrace):
                            raise ValueError(
                                "Input Traces to StationStream must be of subtype "
                                "StationTrace unless an inventory is also provided."
                            )
                    else:
                        if not isinstance(trace, StationTrace):
                            trace = StationTrace(
                                data=trace.data, header=trace.stats, inventory=inventory
                            )
                    self.append(trace)

        self.validate()

    def select(self, *args, **kwargs):
        # super_self = super().select(*args, **kwargs)
        super_self = Stream(self.traces).select(*args, **kwargs)
        selected = self.copy()
        selected.traces = super_self.traces
        return selected

    def validate(self):
        """Validation checks for Traces within a StationStream."""
        # Check that channel codes are unique_npts
        self.__check_channels()

        # Check that id is consistent, and set id if it passes the check.
        self.id = None
        self.__check_id()

        # The ID check is the only one that raises an exception, the
        # rest of these label the stream as failed rather than raise
        # an exception.
        self.__check_sample_rate()
        self.__check_npts()
        self.__check_starts()

    def __check_sample_rate(self):
        unique_sampling_rates = set([tr.stats.sampling_rate for tr in self])
        if len(unique_sampling_rates) > 1:
            for tr in self:
                tr.fail("StationStream traces have different sampling rates.")

    def __check_npts(self):
        unique_npts = set([len(tr) for tr in self])
        if len(unique_npts) > 1:
            for tr in self:
                tr.fail("StationStream traces have a different number of points.")

    def __check_starts(self):
        unique_starts = set([tr.stats.starttime.timestamp for tr in self])
        if len(unique_starts) > 1:
            for tr in self:
                tr.fail("StationStream traces have different start times.")

    def __check_channels(self):
        if len(self):
            all_codes = []
            for tr in self:
                stats = tr.stats
                all_codes.append(f"{stats.network}.{stats.station}.{stats.channel}")
            if len(set(all_codes)) != len(all_codes):
                for tr in self:
                    tr.fail("Nonunique channel code in StationStream.")

    def __check_id(self):
        # Check that id is consistent, and set id if it passes the check.
        if len(self):
            stats = self.traces[0].stats
            if hasattr(self, "use_array") and self.use_array:
                trace = self[0]
                id_str = ".".join(
                    [
                        trace.stats.network,
                        trace.stats.station,
                        trace.stats.location,
                        trace.stats.channel,
                    ],
                )
            else:
                id_str = f"{stats.network}.{stats.station}.{stats.channel[0:2]}"

            # Check that the id would be the same for all traces
            for tr in self:
                stats = tr.stats
                if hasattr(self, "use_array") and self.use_array:
                    test_str = ".".join(
                        [
                            stats.network,
                            stats.station,
                            stats.location,
                            stats.channel,
                        ],
                    )
                else:
                    test_str = f"{stats.network}.{stats.station}.{stats.channel[0:2]}"

                if id_str != test_str:
                    raise ValueError("Inconsistent stream ID for different traces.")
            self.id = id_str

    def get_id(self):
        """Unique identifier for the StationStream.

        For StreamArrays, this is the network, station, location, and channel code.

        For StreamCollections, this is the network, station, and first two characters
        of the channel (to indicate instrument type).
        """
        return self.id

    def get_net_sta(self):
        """Get just the network and station component of the ID."""
        return ".".join(self.get_id().split(".")[0:2])

    def get_net_sta_loc(self):
        """Get network, station, and location codes."""
        stats = self[0].stats
        return ".".join([stats.network, stats.station, stats.location])

    def get_inst(self):
        """Get first two characters of the channel code."""
        return self[0].stats.channel[0:2]

    @property
    def passed(self):
        """Attribute indicating if the stream passed QA checks.

        See `StationStream.check_stream` for more details.

        Returns:
            bool: Stream has passed QA checks.
        """
        return self.check_stream()

    @property
    def num_horizontal(self):
        """Get the number of horizontal components in the StationStream."""
        return len(
            [tr for tr in self if tr.passed and tr.stats.channel[2].upper() != "Z"]
        )

    @property
    def warnings(self):
        """List of unique warnings in the stream's contituent traces."""
        warnings = []
        for trace in self:
            for warning in trace.parameters["warnings"]:
                warnings.append(warning["reason"])
        return list(set(warnings))

    def __str__(self, extended=False, indent=0):
        """String summary of the StationStream.

        Args:
            extended (bool):
                Unused; kept for compatibility with ObsPy parent class.
            indent (int):
                Number of characters to indent.
        """
        if self.traces:
            id_length = self and max(len(tr.id) for tr in self) or 0
        else:
            id_length = 0
        if self.passed:
            pass_str = " (passed)"
        else:
            pass_str = " (failed)"
        ind_str = " " * indent
        out = (
            f"{ind_str}{len(self.traces)} StationTrace(s) in StationStream"
            f"{pass_str}:\n{ind_str}"
        )
        lc = [_i.__str__(id_length, indent) for _i in self]
        out += ("\n" + ind_str).join(lc)
        return out

    def set_stream_param(self, param_id, param_attributes):
        """Add to the StationStreams's set of arbitrary metadata.

        Args:
            param_id (str):
                Key for parameters dictionary.
            param_attributes (dict or list):
                Parameters for the given key.
        """
        self.parameters[param_id] = param_attributes

    def get_stream_param_keys(self):
        """Get a list of all available parameter keys.

        Returns:
            list: List of available parameter keys.
        """
        return list(self.parameters.keys())

    def get_stream_param(self, param_id):
        """Retrieve some arbitrary metadata.

        Args:
            param_id (str):
                Key for parameters dictionary.

        Returns:
            dict or list:
                Parameters for the given key.
        """
        if param_id not in self.parameters:
            raise KeyError(f"Parameter {param_id} not found in StationStream")
        return self.parameters[param_id]

    def get_provenance_documents(self):
        """Generate provenance Document.

        Returns:
            Provenance document.
        """
        provdocs = []
        for trace in self.traces:
            provdocs.append(trace.provenance.to_provenance_document())
        return provdocs

    def get_inventory(self):
        """Extract an ObsPy inventory object from a StationStream."""
        networks = [trace.stats.network for trace in self]
        if len(set(networks)) > 1:
            raise ValueError("Input stream has stations from multiple networks.")

        # We'll first create all the various objects. These strongly follow the
        # hierarchy of StationXML files.
        source = ""
        if "standard" in self[0].stats and "source" in self[0].stats.standard:
            source = self[0].stats.standard.source
        inv = Inventory(
            # We'll add networks later.
            networks=[],
            # The source should be the id whoever create the file.
            source=source,
        )

        net = Network(
            # This is the network code according to the SEED standard.
            code=networks[0],
            # A list of stations. We'll add one later.
            stations=[],
            description="source",
            # Start-and end dates are optional.
        )
        channels = []
        for trace in self:
            channel = _channel_from_stats(trace.stats)
            channels.append(channel)

        sta = Station(
            # This is the station code according to the SEED standard.
            code=self[0].stats.station,
            latitude=self[0].stats.coordinates.latitude,
            elevation=self[0].stats.coordinates.elevation,
            longitude=self[0].stats.coordinates.longitude,
            channels=channels,
            site=Site(name=self[0].stats.standard.station_name),
            creation_date=UTCDateTime(1970, 1, 1),  # this is bogus
            total_number_of_channels=len(self),
        )

        net.stations.append(sta)
        inv.networks.append(net)

        return inv

    def get_supplemental_stats(self):
        """Return dictionary supplemental stream information.

        This was created to include information that is not captured in StationXML
        or in obspy's trace stats object.
        """
        subdict = {}
        for k in UNUSED_STANDARD_PARAMS:
            if k in self[0].stats.standard:
                subdict[k] = self[0].stats.standard[k]

        format_specific = {}
        if "format_specific" in self[0].stats:
            format_specific = dict(self[0].stats.format_specific)
        return {"standard": subdict, "format_specific": format_specific}

    def check_stream(self):
        """Check StationStream for being flagged as failed.

        The logic of this method is controlled by the "any_trace_failures" config
        parameter in the "check_stream" section:
            - If "any_trace_failures" is True, then the stream is treated as failed if
              ANY of the constituent traces failed.
            - If "any_trace_failures" is False, then the tstream is treated as failed
              if ALL of the constituent traces failed.

        Returns:
            bool: True if the stream has passed checks

        """
        any_trace_failures = self.get_stream_param("any_trace_failures")
        failed_traces = []
        for tr in self:
            failed_traces.append(not tr.passed)

        if any_trace_failures:
            if any(failed_traces):
                return False
            else:
                return True
        else:
            if all(failed_traces):
                return False
            else:
                return True


def _channel_from_stats(stats):
    if stats.standard.units_type in constants.UNITS:
        units = constants.UNITS[stats.standard.units_type]
    else:
        units = ""
    instrument = stats.standard.instrument
    serialnum = stats.standard.sensor_serial_number
    if len(instrument) or len(serialnum):
        equipment = Equipment(type=instrument, serial_number=serialnum)
    else:
        equipment = None
    depth = 0.0
    azimuth = None
    c1 = "horizontal_orientation" in stats.standard
    c2 = c1 and not np.isnan(stats.standard.horizontal_orientation)
    if c2:
        azimuth = stats.standard.horizontal_orientation
    else:
        azimuth = 0

    if not (azimuth >= 0 and azimuth <= 360):
        azimuth = 0

    response = None
    if "response" in stats:
        response = stats["response"]
    else:
        # we may have instrument sensitivity...
        frequency = 1 / stats["standard"]["instrument_period"]
        units = stats.standard.units_type
        if not np.isnan(stats["standard"]["instrument_sensitivity"]):
            sens = stats["standard"]["instrument_sensitivity"]
        else:
            sens = 1.0
        sensitivity = InstrumentSensitivity(
            sens, frequency=frequency, input_units=units, output_units="COUNTS"
        )
        response = Response(instrument_sensitivity=sensitivity)

    comments = Comment(stats.standard.comments)
    channel = Channel(
        stats.channel,
        stats.location,
        stats.coordinates["latitude"],
        stats.coordinates["longitude"],
        stats.coordinates["elevation"],
        depth,
        azimuth=azimuth,
        sample_rate=stats.sampling_rate,
        calibration_units=units,
        comments=[comments],
        response=response,
        sensor=equipment,
    )
    return channel
