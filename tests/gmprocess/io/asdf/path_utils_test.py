#!/usr/bin/env pytest
import os

from gmprocess.io.asdf import path_utils
from gmprocess.io.read import read_data
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.utils.config import get_config


def test_path_utils():
    """Unit tests for path utils."""
    EVENTID = "us1000778i"
    LABEL = "ptest"
    datafiles, event = read_data_dir("geonet", EVENTID, "*.V1A")
    stream = read_data(datafiles[0])[0]
    trace = stream[0]
    tag = f"{EVENTID}_{LABEL}"
    config = get_config()

    trace_path = path_utils.get_trace_path(trace, tag)
    trace_name = path_utils.get_trace_name(trace, tag)
    stream_path = path_utils.get_stream_path(stream, tag, config)
    stream_name = path_utils.get_stream_name(stream, tag, config)

    assert trace_path == "NZ.HSES/NZ.HSES.--.HN1_us1000778i_ptest"
    assert trace_name == "NZ.HSES.--.HN1_us1000778i_ptest"
    assert stream_path == "NZ.HSES/NZ.HSES.--.HN_us1000778i_ptest"
    assert stream_name == "NZ.HSES.--.HN_us1000778i_ptest"


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_path_utils()
