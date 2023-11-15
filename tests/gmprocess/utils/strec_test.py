import numpy as np
import pytest

from obspy.core.utcdatetime import UTCDateTime
from obspy.core.event.magnitude import Magnitude
from obspy.core.event.origin import Origin

from gmprocess.utils import event_utils
from gmprocess.utils import strec
from gmprocess.utils import test_utils


@pytest.fixture
def setup_event():
    eid = "usp000hat0"
    time = UTCDateTime("2010-04-06 22:15:01.580")
    lat = 2.383
    lon = 97.048
    depth = 31.0
    mag = 7.8

    event = event_utils.ScalarEvent.from_params(eid, time, lat, lon, depth * 1000, mag)
    return event


@test_utils.vcr.use_cassette()
def test_strec(setup_event, tmp_path):
    strec_info = strec.STREC.from_event(setup_event)
    assert strec_info.results["TectonicRegion"] == "Subduction"
    assert strec_info.results["FocalMechanism"] == "RS"
    np.testing.assert_allclose(
        strec_info.results["DistanceToActive"], 145.2935045889962
    )

    json_file = tmp_path / "strec_test.json"
    strec_info.to_file(json_file)
    strec_info2 = strec.STREC.from_file(json_file)
    np.testing.assert_allclose(
        strec_info2.results["DistanceToActive"], 145.2935045889962
    )
