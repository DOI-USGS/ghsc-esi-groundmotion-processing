import shutil
import datetime

import pytz

from obspy.core.utcdatetime import UTCDateTime

from gmprocess.utils import download_utils
from gmprocess.utils import test_utils


EVENT_INFO = {
    "id": "usp000hat0",
    "time": UTCDateTime("2010-04-06 22:15:01.580"),
    "lat": 2.383,
    "lon": 97.048,
    "depth_km": 31.0,
    "magnitude": 7.8,
    "mag_type": "mwc",
}


@test_utils.vcr.use_cassette()
def abc_test_download_comcat_event():
    data = download_utils.download_comcat_event(eventid="usp000hat0")
    assert data["id"] == EVENT_INFO["id"]
    assert data["geometry"]["coordinates"][0] == EVENT_INFO["lon"]
    assert data["geometry"]["coordinates"][1] == EVENT_INFO["lat"]
    assert data["geometry"]["coordinates"][2] == EVENT_INFO["depth_km"]
    assert data["properties"]["mag"] == EVENT_INFO["magnitude"]
    assert data["properties"]["magType"] == EVENT_INFO["mag_type"]
    origin_time = UTCDateTime(
        datetime.datetime.fromtimestamp(data["properties"]["time"] / 1000.0, pytz.utc)
    )
    assert origin_time == EVENT_INFO["time"]


def test_download_waveforms():
    return


def test_download_rupture_file():
    return
