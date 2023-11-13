import numpy as np
import pytest

from obspy.core.utcdatetime import UTCDateTime
from obspy.core.event.magnitude import Magnitude
from obspy.core.event.origin import Origin

from gmprocess.utils.event import ScalarEvent
from gmprocess.utils.strec import STREC
from gmprocess.utils.test_utils import vcr


@pytest.fixture
def setup_event():
    eid = "usp000hat0"
    time = UTCDateTime("2010-04-06 22:15:01.580")
    lat = 2.383
    lon = 97.048
    depth = 31.0
    mag = 7.8
    mag_type = "Mwc"

    event = ScalarEvent()
    origin = Origin(
        resource_id=eid, time=time, latitude=lat, longitude=lon, depth=depth * 1000
    )
    magnitude = Magnitude(mag=mag, magnitude_type=mag_type)
    event.origins = [origin]
    event.magnitudes = [magnitude]
    return event


@vcr.use_cassette()
def test_strec(setup_event, tmp_path):
    strec = STREC.from_event(setup_event)
    assert strec.results["TectonicRegion"] == "Subduction"
    assert strec.results["FocalMechanism"] == "RS"
    np.testing.assert_allclose(strec.results["DistanceToActive"], 145.2935045889962)

    json_file = tmp_path / "strec_test.json"
    print(json_file)
    strec.to_file(json_file)
    strec2 = STREC.from_file(json_file)
    np.testing.assert_allclose(strec2.results["DistanceToActive"], 145.2935045889962)
