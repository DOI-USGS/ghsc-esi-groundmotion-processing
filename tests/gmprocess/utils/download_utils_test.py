import datetime
import json

import pytz

from obspy.core.utcdatetime import UTCDateTime

from gmprocess.core import scalar_event
from gmprocess.utils import constants
from gmprocess.utils import download_utils
from gmprocess.utils import test_utils


EVENT_INFO = {
    "id": "us20005iis",
    "time": UTCDateTime("2016-04-15 16:25:06.220"),
    "latitude": 32.7906,
    "longitude": 130.7543,
    "depth_km": 10.0,
    "magnitude": 7.0,
    "magnitude_type": "mww",
}


@test_utils.vcr.use_cassette()
def test_download_comcat_event():
    data = download_utils.download_comcat_event(EVENT_INFO["id"])
    assert data["id"] == EVENT_INFO["id"]
    assert data["geometry"]["coordinates"][0] == EVENT_INFO["longitude"]
    assert data["geometry"]["coordinates"][1] == EVENT_INFO["latitude"]
    assert data["geometry"]["coordinates"][2] == EVENT_INFO["depth_km"]
    assert data["properties"]["mag"] == EVENT_INFO["magnitude"]
    assert data["properties"]["magType"] == EVENT_INFO["magnitude_type"]
    origin_time = UTCDateTime(
        datetime.datetime.fromtimestamp(data["properties"]["time"] / 1000.0, pytz.utc)
    )
    assert origin_time == EVENT_INFO["time"]


@test_utils.vcr.use_cassette()
def test_download_rupture_file():
    EVENT_ID = "ci38457511"

    data_dir = constants.TEST_DATA_DIR
    download_utils.download_rupture_file(EVENT_ID, data_dir)

    file_path = data_dir / constants.RUPTURE_FILE
    assert file_path.is_file()
    with open(file_path, encoding="utf-8") as fin:
        data = json.load(fin)
        assert data["metadata"]["id"] == EVENT_ID
    file_path.unlink()


@test_utils.vcr.use_cassette()
def test_get_strec_results():
    data_dir = constants.TEST_DATA_DIR
    event = scalar_event.ScalarEvent.from_params(**EVENT_INFO)
    download_utils.get_strec_results(event, data_dir)

    file_path = data_dir / constants.STREC_FILE
    assert file_path.is_file()
    with open(file_path, encoding="utf-8") as fin:
        data = json.load(fin)
        assert data["TectonicRegion"] == "Subduction"
        assert data["SlabModelRegion"] == "Ryukyu"
    file_path.unlink()
