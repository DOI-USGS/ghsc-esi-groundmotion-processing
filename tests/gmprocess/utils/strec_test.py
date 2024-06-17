import numpy as np
import pytest

from obspy.core.utcdatetime import UTCDateTime

from gmprocess.utils.strec import STREC
from gmprocess.core import scalar_event
from gmprocess.utils import tests_utils


@pytest.fixture
def setup_event():
    eid = "usp000hat0"
    time = UTCDateTime("2010-04-06 22:15:01.580")
    lat = 2.383
    lon = 97.048
    depth = 31.0
    mag = 7.8

    event = scalar_event.ScalarEvent.from_params(
        eid, time, lat, lon, depth, mag
    )
    return event


@tests_utils.vcr.use_cassette()
def test_strec(setup_event, tmp_path):
    strec = STREC.from_event(setup_event)
    assert strec.results["TectonicRegion"] == "Subduction"
    assert strec.results["FocalMechanism"] == "RS"
    np.testing.assert_allclose(
        strec.results["DistanceToActive"], 145.2935045889962
    )

    json_file = tmp_path / "strec_test.json"
    strec.to_file(json_file)
    strec2 = STREC.from_file(json_file)
    np.testing.assert_allclose(
        strec2.results["DistanceToActive"], 145.2935045889962
    )
