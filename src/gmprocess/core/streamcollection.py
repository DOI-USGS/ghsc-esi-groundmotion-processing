"""Module for StreamCollection class.

This class functions as a list of StationStream objects, and enforces
various rules, such as all traces within a stream are from the same station.
"""

import re
import logging

from obspy import UTCDateTime
from obspy.geodetics import gps2dist_azimuth
import pandas as pd
import numpy as np

from gmprocess.core.streamarray import StreamArray
from gmprocess.core.stationstream import StationStream
from gmprocess.core.stationtrace import REV_PROCESS_LEVELS
from gmprocess.io.read_directory import directory_to_streams
from gmprocess.utils.config import get_config


INDENT = 2

DEFAULT_IMTS = ["PGA", "PGV", "SA(0.3)", "SA(1.0)", "SA(3.0)"]
DEFAULT_IMCS = ["GREATER_OF_TWO_HORIZONTALS", "CHANNELS"]

NETWORKS_USING_LOCATION = ["RE"]


class StreamCollection(StreamArray):
    """A collection/list of StationStream objects.

    This is a list of StationStream objects, where the constituent
    StationTraces are grouped such that:

        - All traces are from the same network/station/instrument.
        - Sample rates must match.
        - Units much match.

    TODO:
        - Check for and handle misaligned start times and end times.
        - Check units
    """

    def __init__(
        self,
        streams=None,
        drop_non_free=True,
        handle_duplicates=True,
        max_dist_tolerance=None,
        preference_order=None,
        process_level_preference=None,
        format_preference=None,
        config=None,
    ):
        """Initialize StreamCollection.

        Args:
            streams (list):
                List of StationStream objects.
            drop_non_free (bool):
                If True, drop non-free-field Streams from the collection.
            handle_duplicates (bool):
                If True, remove duplicate data from the collection.
            max_dist_tolerance (float):
                Maximum distance tolerance for determining whether two streams
                are at the same location (in meters).
            preference_order (list):
                A list containing 'process_level', 'source_format',
                'starttime', 'npts', 'sampling_rate', 'location_code' in the
                desired order for choosing the preferred trace.
            process_level_preference (list):
                A list containing 'V0', 'V1', 'V2', with the order determining
                which process level is the most preferred (most preferred goes
                first in the list).
            format_preference (list):
                A list containing strings of the file source formats (found
                in gmprocess.io). Does not need to list all of the formats.
                Example: ['cosmos', 'dmg'] indicates that cosmos files are
                preferred over dmg files.
            config (dict):
                Configuration options.
        """
        self.config = config
        # Some initial checks of input streams
        if not isinstance(streams, list):
            raise TypeError("streams must be a list of StationStream objects.")
        newstreams = []
        for st in streams:
            if not isinstance(st, StationStream):
                raise TypeError("streams must be a list of StationStream objects.")

            st.id = st.get_id()
            st.use_array = False

            if drop_non_free:
                if st[0].free_field:
                    newstreams.append(st)
                else:
                    logging.info(
                        "Omitting station trace %s from stream collection "
                        "because it is not free field.",
                        st[0].id,
                    )
            else:
                newstreams.append(st)

        self.streams = newstreams
        if handle_duplicates:
            if self.streams:
                self.__handle_duplicates(
                    max_dist_tolerance,
                    preference_order,
                    process_level_preference,
                    format_preference,
                )
        self.__group_by_net_sta_inst()
        self.validate()

    def validate(self):
        """Some validation checks across streams."""
        # If tag exists, it should be consistent across StationStreams
        all_labels = []
        for stream in self:
            if hasattr(stream, "tag"):
                parts = stream.tag.split("_")
                if len(parts) > 2:
                    label = parts[-1]
                else:
                    label = stream.tag.split("_")[-1]
                all_labels.append(label)
            else:
                all_labels.append("")
        if len(set(all_labels)) > 1:
            raise ValueError("Only one label allowed within a StreamCollection.")

    def select_colocated(
        self, preference=["HN?", "BN?", "HH?", "BH?"], large_dist=None, event=None
    ):
        """Detect colocated instruments, return preferred instrument type.

        This uses the list of the first two channel characters, given as
        'preference' in the 'colocated' section of the config. The algorithm
        is:

            1) Generate list of StationStreams that have the same station code.
            2) For each colocated group, loop over the list of preferred
               instrument codes, select the first one that is encountered by
               labeling all others a failed.

                * If the preferred instrument type matches more than one
                  StationStream, pick the first (hopefully this never happens).
                * If no StationStream matches any of the codes in the preferred
                  list then label all as failed.

        Args:
            preference (list):
                List of strings indicating preferred instrument types.
            large_dist (dict):
                A dictionary with keys "preference", "mag", and "dist";
                "preference" is the same as the "preference" argument to this
                function, but will replace it when the distance is exceeded
                for a given magnitude. The distance threshold is computed as:

                    ```
                    dist_thresh = dist[0]
                    for m, d in zip(mag, dist):
                        if eqmag > m:
                            dist_thresh = d
                    ```

            event (gmprocess.core.scalar_event.ScalarEvent):
                A ScalarEvent object.
        """
        # Do we have different large distnce preference?
        if large_dist is not None and large_dist["enabled"]:
            dist_thresh = large_dist["dist"][0]
            for m, d in zip(large_dist["mag"], large_dist["dist"]):
                if event.magnitude > m:
                    dist_thresh = d

        # Create a dict of colocated streams.
        # net_sta -> array of indices for matching stations in stream
        match_list = {}
        for i_st, stream in enumerate(self):
            if not stream.passed:
                continue
            net_sta = stream.get_net_sta()
            if not net_sta in match_list:
                match_list[net_sta] = [i_st]
            else:
                match_list[net_sta].append(i_st)

        for group in match_list.values():
            # Are there colocated instruments for this group?
            if len(group) > 1:
                # If so, loop over list of preferred instruments
                group_insts = [self[g].get_inst() for g in group]

                if large_dist and large_dist["enabled"]:
                    tr = self[group[0]][0]
                    distance = (
                        gps2dist_azimuth(
                            tr.stats.coordinates.latitude,
                            tr.stats.coordinates.longitude,
                            event.latitude,
                            event.longitude,
                        )[0]
                        / 1000.0
                    )

                    if distance > dist_thresh:
                        preference = large_dist["preference"]

                # Loop over preferred instruments
                no_match = True
                for pref in preference:
                    # Is this instrument available in the group?
                    r = re.compile(pref[0:2])
                    inst_match = list(filter(r.match, group_insts))
                    if len(inst_match):
                        no_match = False
                        # Select index; if more than one, we just take the
                        # first one because we don't know any better
                        keep = inst_match[0]

                        # Label all non-selected streams in the group as failed
                        to_fail = group_insts
                        to_fail.remove(keep)
                        for tf in to_fail:
                            for st in self.select(
                                network=self[group[0]][0].stats.network,
                                station=self[group[0]][0].stats.station,
                                instrument=tf,
                            ):
                                for tr in st:
                                    tr.fail(f"Colocated with {keep} instrument.")

                        break
                if no_match:
                    # Fail all Streams in group
                    for g in group:
                        for tr in self[g]:
                            tr.fail(
                                "No instruments match entries in the "
                                "colocated instrument preference list for "
                                "this station."
                            )

    @classmethod
    def from_directory(cls, directory):
        """Create a StreamCollection instance from a directory of data.

        Args:
            directory (str):
                Directory of ground motion files (streams) to be read.
            use_default_config (bool):
                Use default ("production") config.

        Returns:
            StreamCollection instance.
        """
        config = get_config()
        streams, _, _ = directory_to_streams(directory, config=config)

        # Might eventually want to include some of the missed files and
        # error info but don't have a sensible place to put it currently.
        return cls(streams, config=config)

    @classmethod
    def from_traces(cls, traces, config=None):
        """Create a StreamCollection instance from a list of traces.

        Args:
            traces (list):
                List of StationTrace objects.

        Returns:
            StreamCollection instance.
        """

        streams = [StationStream([tr], config=config) for tr in traces]
        return cls(streams, config=config)

    def __str__(self):
        """String summary of the StreamCollection."""
        summary = ""
        n = len(self.streams)
        summary += f"{n} StationStreams(s) in StreamCollection:\n"
        summary += f"    {self.n_passed} StationStreams(s) passed checks.\n"
        summary += f"    {self.n_failed} StationStreams(s) failed checks.\n"
        return summary

    def describe_string(self):
        """More verbose description of StreamCollection."""
        lines = [""]
        lines += [str(len(self.streams)) + " StationStreams(s) in StreamCollection:"]
        for stream in self:
            lines += [stream.__str__(indent=INDENT)]
        return "\n".join(lines)

    def describe(self):
        """Thin wrapper of describe_string() for printing to stdout"""
        stream_descript = self.describe_string()
        print(stream_descript)

    def __group_by_net_sta_inst(self):
        trace_list = []
        stream_params = gather_stream_parameters(self.streams)
        for st in self.streams:
            for tr in st:
                trace_list.append(tr)

        # Create a list of traces with matching net, sta.
        all_matches = []
        match_list = []
        for idx1, trace1 in enumerate(trace_list):
            if idx1 in all_matches:
                continue
            matches = [idx1]
            network = trace1.stats["network"]
            station = trace1.stats["station"]
            free_field = trace1.free_field
            # For instrument, use first two characters of the channel
            inst = trace1.stats["channel"][0:2]
            for idx2, trace2 in enumerate(trace_list):
                if idx1 != idx2 and idx1 not in all_matches:
                    if (
                        network == trace2.stats["network"]
                        and station == trace2.stats["station"]
                        and inst == trace2.stats["channel"][0:2]
                        and free_field == trace2.free_field
                    ):
                        matches.append(idx2)
            if len(matches) > 1:
                match_list.append(matches)
                all_matches.extend(matches)
            else:
                if matches[0] not in all_matches:
                    match_list.append(matches)
                    all_matches.extend(matches)

        grouped_streams = []
        for groups in match_list:
            grouped_trace_list = []
            for i in groups:
                grouped_trace_list.append(trace_list[i])
            # some networks (e.g., Bureau of Reclamation, at the time of this
            # writing) use the location field to indicate different sensors at
            # (roughly) the same location. If we know this (as in the case of
            # BOR), we can use this to trim the stations into 3-channel
            # streams.
            streams = split_station(grouped_trace_list, config=self.config)
            streams = insert_stream_parameters(streams, stream_params)

            for st in streams:
                grouped_streams.append(st)

        self.streams = grouped_streams

    def __handle_duplicates(
        self,
        max_dist_tolerance,
        preference_order,
        process_level_preference,
        format_preference,
    ):
        """
        Removes duplicate data from the StreamCollection, based on the
        process level and format preferences.

        Args:
            max_dist_tolerance (float):
                Maximum distance tolerance for determining whether two streams
                are at the same location (in meters).
            preference_order (list):
                A list containing 'process_level', 'source_format',
                'starttime', 'npts', 'sampling_rate', 'location_code' in the
                desired order for choosing the preferred trace.
            process_level_preference (list):
                A list containing 'V0', 'V1', 'V2', with the order determining
                which process level is the most preferred (most preferred goes
                first in the list).
            format_preference (list):
                A list continaing strings of the file source formats (found
                in gmprocess.io). Does not need to list all of the formats.
                Example: ['cosmos', 'dmg'] indicates that cosmos files are
                preferred over dmg files.
        """

        # Note, that self.config will not exist in some circumstanses, so we need to
        # provide defaults.

        preferences = {
            "max_dist_tolerance": max_dist_tolerance,
            "preference_order": preference_order,
            "process_level_preference": process_level_preference,
            "format_preference": format_preference,
        }

        # Set the values from the config if it exists:
        if hasattr(self, "config") and self.config is not None:
            for key, val in preferences.items():
                if val is None:
                    preferences[key] = self.config["duplicate"][key]
        else:
            # Set to defaults:
            preferences["max_dist_tolerance"] = 500.0
            preferences["preference_order"] = [
                "process_level",
                "source_format",
                "starttime",
                "npts",
                "sampling_rate",
                "location_code",
            ]
            preferences["process_level_preference"] = ["V1", "V0", "V2"]
            preferences["format_preference"] = ["cosmos", "dmg"]
        stream_params = gather_stream_parameters(self.streams)

        traces = []
        for st in self.streams:
            traces += [tr for tr in st]
        preferred_traces = []

        for tr_to_add in traces:
            is_duplicate = False
            for tr_pref in preferred_traces:
                if are_duplicates(
                    tr_to_add, tr_pref, preferences["max_dist_tolerance"]
                ):
                    is_duplicate = True
                    break

            if is_duplicate:
                if (
                    choose_preferred(
                        tr_to_add,
                        tr_pref,
                        preferences["preference_order"],
                        preferences["process_level_preference"],
                        preferences["format_preference"],
                    )
                    == tr_to_add
                ):
                    preferred_traces.remove(tr_pref)
                    logging.info(
                        "Trace %s (%s) is a duplicate and "
                        "has been removed from the StreamCollection.",
                        tr_pref.id,
                        tr_pref.stats.standard.source_file,
                    )
                    preferred_traces.append(tr_to_add)
                else:
                    logging.info(
                        "Trace %s (%s) is a duplicate and "
                        "has been removed from the StreamCollection.",
                        tr_to_add.id,
                        tr_to_add.stats.standard.source_file,
                    )

            else:
                preferred_traces.append(tr_to_add)

        streams = [StationStream([tr], config=self.config) for tr in preferred_traces]
        streams = insert_stream_parameters(streams, stream_params)
        self.streams = streams

    def get_status(self, status):
        """Returns a summary of the status of the streams in StreamCollection.

        If status='short': Returns a two column table, columns are "Failure
            Reason" and "Number of Records". Number of rows is the number of
            unique failure reasons.
        If status='net': Returns a three column table, columns are "Network",
            "Number Passed", and "Number Failed"; number of rows is the number
            of unique networks.
        If status='long': Returns a two column table, columns are "StationID"
            and "Failure Reason".

        Args:
            status (str):
                The status level (see description).

        Returns:
            If status='net': pandas.DataFrame
            If status='short' or status='long': pandas.Series
        """

        if status == "short":
            failure_reasons = pd.Series(
                [
                    next(tr for tr in st if not tr.passed).get_parameter("failure")[
                        "reason"
                    ]
                    for st in self.streams
                    if not st.passed
                ],
                dtype=str,
            )
            failure_counts = failure_reasons.value_counts()
            failure_counts.name = "Number of Records"
            failure_counts.index.name = "Failure Reason"
            return failure_counts
        elif status == "net":
            failure_dict = {}
            for st in self.streams:
                net = st[0].stats.network
                if net not in failure_dict:
                    failure_dict[net] = {"Number Passed": 0, "Number Failed": 0}
                if st.passed:
                    failure_dict[net]["Number Passed"] += 1
                else:
                    failure_dict[net]["Number Failed"] += 1
            df = pd.DataFrame.from_dict(failure_dict).transpose()
            df.index.name = "Network"
            return df
        elif status == "long":
            failure_reasons = []
            for st in self.streams:
                if not st.passed:
                    first_failure = next(tr for tr in st if not tr.passed)
                    first_reason = first_failure.get_parameter("failure")["reason"]
                    failure_reasons.append(f"failed ({first_reason})")
                else:
                    failure_reasons.append("passed")
            sta_ids = [st.id for st in self.streams]
            failure_srs = pd.Series(index=sta_ids, data=failure_reasons, name="Status")
            failure_srs.index.name = "StationID"
            return failure_srs
        else:
            raise ValueError('Status must be "short", "net", or "long".')


def gather_stream_parameters(streams):
    """
    Helper function for gathering the stream parameters into a datastructure
    and sticking the stream tag into the trace stats dictionaries.

    Args:
        streams (list):
            list of StationStream objects.

    Returns:
        dict. Dictionary of the stream parameters.
    """
    stream_params = {}

    # Need to make sure that tag will be preserved; tag only really should
    # be created once a StreamCollection has been written to an ASDF file
    # and then read back in.
    for stream in streams:
        # we have stream-based metadata that we need to preserve
        if len(stream.parameters):
            stream_params[stream.get_id()] = stream.parameters

        # Tag is a StationStream attribute; If it does not exist, make it
        # an empty string
        if hasattr(stream, "tag"):
            tag = stream.tag
        else:
            tag = ""
        # Since we have to deconstruct the stream groupings each time, we
        # need to stick the tag into the trace stats dictionary temporarily
        for trace in stream:
            tr = trace
            tr.stats.tag = tag

    return stream_params


def insert_stream_parameters(streams, stream_params):
    """Helper function for inserting the stream parameters back to the streams.

    Args:
        streams (list):
            list of StationStream objects.
        stream_params (dict):
            Dictionary of stream parameters.

    Returns:
        list of StationStream objects with stream parameters.
    """
    for st in streams:
        if len(st):
            sid = st.get_id()
            # put stream parameters back in
            if sid in stream_params:
                st.parameters = stream_params[sid].copy()

            # Put tag back as a stream attribute, assuming that the
            # tag has stayed the same through the grouping process
            if st[0].stats.tag:
                st.tag = st[0].stats.tag

    return streams


def split_station(grouped_trace_list, config):
    if grouped_trace_list[0].stats.network in NETWORKS_USING_LOCATION:
        streams_dict = {}
        for trace in grouped_trace_list:
            if trace.stats.location in streams_dict:
                streams_dict[trace.stats.location] += trace
            else:
                streams_dict[trace.stats.location] = StationStream(
                    traces=[trace], config=config
                )
        streams = list(streams_dict.values())
    else:
        streams = [StationStream(traces=grouped_trace_list, config=config)]
    return streams


def are_duplicates(tr1, tr2, max_dist_tolerance):
    """Check if traces are duplicates.

    Determines whether two StationTraces are duplicates by checking the
    station, channel codes, and the distance between them.

    Args:
        tr1 (StationTrace):
            1st trace.
        tr2 (StationTrace):
            2nd trace.
        max_dist_tolerance (float):
            Maximum distance tolerance for determining whether two streams
            are at the same location (in meters).

    Returns:
        bool. True if traces are duplicates, False otherwise.
    """
    orientation_codes = set()
    for tr in [tr1, tr2]:
        if tr.stats.channel[2] in ["1", "N"]:
            orientation_codes.add("1")
        elif tr.stats.channel[2] in ["2", "E"]:
            orientation_codes.add("2")
        else:
            orientation_codes.add("Z")

    # First, check if the ids match (net.sta.loc.cha)
    if tr1.id[:-1] == tr2.id[:-1] and len(orientation_codes) == 1:
        return True
    # If not matching IDs, check the station, instrument code, and distance
    else:
        distance = gps2dist_azimuth(
            tr1.stats.coordinates.latitude,
            tr1.stats.coordinates.longitude,
            tr2.stats.coordinates.latitude,
            tr2.stats.coordinates.longitude,
        )[0]
        if (
            tr1.stats.station == tr2.stats.station
            and tr1.stats.channel[:2] == tr2.stats.channel[:2]
            and len(orientation_codes) == 1
            and distance < max_dist_tolerance
        ):
            return True
        else:
            return False


def choose_preferred(
    tr1, tr2, preference_order, process_level_preference, format_preference
):
    """Determines which trace is preferred. Returns the preferred trace.

    Args:
        tr1 (StationTrace):
            1st trace.
        tr2 (StationTrace):
            2nd trace.
        preference_order (list):
            A list containing 'process_level', 'source_format', 'starttime',
            'npts', 'sampling_rate', 'location_code' in the desired order
            for choosing the preferred trace.
        process_level_preference (list):
            A list containing 'V0', 'V1', 'V2', with the order determining
            which process level is the most preferred (most preferred goes
            first in the list).
        format_preference (list):
            A list continaing strings of the file source formats (found
            in gmprocess.io). Does not need to list all of the formats.
            Example: ['cosmos', 'dmg'] indicates that cosmos files are
            preferred over dmg files.

    Returns:
        The preferred trace (StationTrace).
    """
    traces = [tr1, tr2]
    for pref in preference_order:
        if pref == "process_level":
            tr_prefs = [
                process_level_preference.index(
                    REV_PROCESS_LEVELS[tr.stats.standard.process_level]
                )
                for tr in traces
            ]
        elif pref == "source_format":
            if all(
                [tr.stats.standard.source_format in format_preference for tr in traces]
            ):
                tr_prefs = [
                    format_preference.index(tr.stats.standard.source_format)
                    for tr in traces
                ]
            else:
                continue
        elif pref == "starttime":
            tr_prefs = [tr.stats.starttime == UTCDateTime(0) for tr in traces]
        elif pref == "npts":
            tr_prefs = [1 / tr.stats.npts for tr in traces]
        elif pref == "sampling_rate":
            tr_prefs = [1 / tr.stats.sampling_rate for tr in traces]
        elif pref == "location_code":
            sorted_codes = sorted([tr.stats.location for tr in traces])
            tr_prefs = [
                (
                    sorted_codes.index(tr.stats.location)
                    if tr.stats.location != "--"
                    else np.nan
                )
                for tr in traces
            ]

        if len(set(tr_prefs)) != 1:
            return traces[np.nanargmin(tr_prefs)]
    return tr1
