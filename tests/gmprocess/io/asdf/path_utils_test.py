from gmprocess.io.asdf import path_utils


def test_path_utils(load_data_us1000778i, config):
    """Unit tests for path utils."""
    EVENTID = "us1000778i"
    LABEL = "ptest"
    streams, _ = load_data_us1000778i
    stream = streams.select(station="HSES")[0]
    trace = [tr for tr in stream if tr.stats.channel == "HN1"][0]
    tag = f"{EVENTID}_{LABEL}"

    trace_path = path_utils.get_trace_path(trace, tag)
    trace_name = path_utils.get_trace_name(trace, tag)
    stream_path = path_utils.get_stream_path(stream, tag, config)
    stream_name = path_utils.get_stream_name(stream, tag, config)

    assert trace_path == "NZ.HSES/NZ.HSES.--.HN1_us1000778i_ptest"
    assert trace_name == "NZ.HSES.--.HN1_us1000778i_ptest"
    assert stream_path == "NZ.HSES/NZ.HSES.--.HN_us1000778i_ptest"
    assert stream_name == "NZ.HSES.--.HN_us1000778i_ptest"
