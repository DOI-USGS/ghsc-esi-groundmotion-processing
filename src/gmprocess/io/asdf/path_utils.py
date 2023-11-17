"""Utility module for handling stream paths for the HDF file

This is used in a few different places, which is why it is useful to break it out
into a separate module that can be re-used.
"""


def get_trace_name(trace, tag):
    """Get a unique `name` for a trace, used in multiple places.

    Examples:
      - `name` argument for the `add_provenance_document` function.
      - Sub-group name for:
          - auxiliary_data/Cache
          - provenance
          - auxiliary_data/TraceProcessingParameters
          - auxiliary_data/review

    Args:
        trace (StationTrace):
            A stationTrace object.
        tag (str):
            The "tag", which is formatted as "{eventid}_{label}" for waveform metrics,
            and just eventid for station metrics.

    Returns:
        str: Trace name.
    """
    return format_nslct(trace.stats, tag)


def get_trace_path(trace, tag):
    """Get the trace path for use in TraceProcessingPrameters

    Args:
        trace (StationTrace):
            A stationTrace object.
        tag (str):
            The "tag", which is formatted as "{eventid}_{label}" for waveform metrics,
            and just eventid for station metrics.

    Returns:
        str: Trace path.
    """
    trace_name = get_trace_name(trace, tag)
    net = trace.stats.network
    sta = trace.stats.station
    trace_path = f"{net}.{sta}/{trace_name}"
    return trace_path


def get_stream_name(stream, tag, config):
    """Get stream name

    Args:
        stream (StationStream):
            A stream.
        tag (str):
            The "tag", which is formatted as "{eventid}_{label}" for waveform metrics,
            and just eventid for station metrics.
        config (dict):
            Dictionary of config options.

    Returns:
        str: Stream name.
    """
    if config["read"]["use_streamcollection"]:
        chancode = stream.get_inst()
    else:
        chancode = stream[0].stats.channel

    stream_name = format_nslit(stream[0].stats, chancode, tag)

    return stream_name


def get_stream_path(stream, tag, config):
    """Get the stream path for use in AuxiliaryData.

    Args:
        stream (StationStream):
            A stream.
        tag (str):
            The "tag", which is formatted as "{eventid}_{label}" for waveform metrics,
            and just eventid for station metrics.
        config (dict):
            Dictionary of config options.

    Returns:
        str: Stream path.
    """
    stream_name = get_stream_name(stream, tag, config)
    net = stream[0].stats.network
    sta = stream[0].stats.station
    stream_path = f"{net}.{sta}/{stream_name}"
    return stream_path


def format_nslc(stats):
    """Convenience method to get period-separated NSLC codes"""
    return "{st.network}.{st.station}.{st.location}.{st.channel}".format(st=stats)


def format_nslct(stats, tag):
    """Convenience method to get period-separated NSLC code with tag appended"""
    return format_nslc(stats) + "_" + tag


def format_nslit(stats, inst, tag):
    """Convenience method to get period-separated NSLI code with tag appended.

    Note that "I" is the instrument code, i.e., first two characters of channel code.
    """
    return "{st.network}.{st.station}.{st.location}.{inst}_{tag}".format(
        st=stats, inst=inst, tag=tag
    )
