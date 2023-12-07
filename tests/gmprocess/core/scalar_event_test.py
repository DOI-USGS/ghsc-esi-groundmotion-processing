import json
import shutil

from obspy.core.event import read_events
from obspy.core.utcdatetime import UTCDateTime

from gmprocess.core import scalar_event
from gmprocess.utils import constants


EVENT_INFO = {
    "id": "usp000hat0",
    "time": UTCDateTime("2010-04-06 22:15:01.580"),
    "latitude": 2.383,
    "longitude": 97.048,
    "depth_km": 31.0,
    "magnitude": 7.8,
    "magnitude_type": "mwc",
}
EVENT_IDS = [
    "ci38445975",
    "ci38457511",
    "nc51194936",
    "nc72282711",
    "nc73300395",
    "se60247871",
    "us70008dx7",
    "uu60363602",
    "uw61251926",
]


def check_event(event, expected):
    assert event.id == expected["id"]
    assert event.time == expected["time"]
    assert event.latitude == expected["latitude"]
    assert event.longitude == expected["longitude"]
    assert event.depth_km == expected["depth_km"]
    assert event.magnitude == expected["magnitude"]
    assert event.magnitude_type.lower() == expected["magnitude_type"]


def test_scalar_fromobspy():
    quakeml = constants.TEST_DATA_DIR / "usp000hat0_quakeml.xml"
    obspy_event = read_events(str(quakeml))[0]
    event = scalar_event.ScalarEvent.from_obspy(obspy_event)
    expected = EVENT_INFO.copy()
    expected["id"] = "quakeml:us.anss.org/origin/pde20100406221501580_31"
    check_event(event, expected)


def test_scalar_fromparams():
    event = scalar_event.ScalarEvent.from_params(**EVENT_INFO)
    check_event(event, EVENT_INFO)


def test_scalar_fromworkspace():
    EVENT_INFO = {
        "id": "nc71126864",
        "time": UTCDateTime("2021-12-20T20:13:40.75"),
        "latitude": 40.3498333,
        "longitude": -124.8993333,
        "depth_km": 19.88,
        "magnitude": 4.84,
        "magnitude_type": "ml",
    }
    filename = (
        constants.TEST_DATA_DIR / "asdf" / "nc71126864" / constants.WORKSPACE_NAME
    )
    event = scalar_event.ScalarEvent.from_workspace(filename)
    check_event(event, EVENT_INFO)


def test_scalar_from_geojson():
    filename = constants.TEST_DATA_DIR / "usp000hat0.geojson"
    event = scalar_event.ScalarEvent.from_json(filename)
    check_event(event, EVENT_INFO)


def test_scalar_from_json():
    filename = constants.TEST_DATA_DIR / "usp000hat0.json"
    event = scalar_event.ScalarEvent.from_json(filename)
    check_event(event, EVENT_INFO)


def test_scalar_to_json():
    event = scalar_event.ScalarEvent.from_params(**EVENT_INFO)

    scratch_dir = constants.TEST_DATA_DIR / "scratch"
    scratch_dir.mkdir(exist_ok=True)
    event.to_json(scratch_dir)
    event_new = scalar_event.ScalarEvent.from_json(scratch_dir / "event.json")
    event = scalar_event.ScalarEvent.from_params(**EVENT_INFO)
    assert event_new == event
    # shutil.rmtree(scratch_dir)


def test_get_event_ids():
    # From list
    event_ids = scalar_event.get_event_ids(ids=EVENT_IDS)
    assert EVENT_IDS == event_ids

    # from file
    filename = constants.TEST_DATA_DIR / "fdsn" / "event_ids.txt"
    event_ids = scalar_event.get_event_ids(filename=filename)
    assert EVENT_IDS == event_ids

    # from directories
    data_dir = constants.TEST_DATA_DIR / "fdsn"
    event_ids = scalar_event.get_event_ids(data_dir=data_dir)
    assert EVENT_IDS == event_ids

    # list, not file
    filename = constants.TEST_DATA_DIR / "fdsn" / "event_ids.txt"
    event_ids = scalar_event.get_event_ids(ids=EVENT_IDS[0:5], filename=filename)
    assert EVENT_IDS[0:5] == event_ids

    # file, not directories
    filename = constants.TEST_DATA_DIR / "event_ids.txt"
    data_dir = constants.TEST_DATA_DIR / "fdsn"
    event_ids = scalar_event.get_event_ids(filename=filename, data_dir=data_dir)
    assert EVENT_IDS[0:2] == event_ids


def test_parse_events_file():
    # File with event ids
    filename = constants.TEST_DATA_DIR / "fdsn" / "event_ids.txt"
    event_ids = scalar_event.parse_events_file(filename=filename)
    assert EVENT_IDS == event_ids

    # File with event information
    EVENTS_DETAIL = [
        scalar_event.ScalarEvent.from_params(
            "ci38445975", "2019-07-05T00:18:01.410", 35.772, -117.618, 2.6, 4.04, "mw"
        ),
        scalar_event.ScalarEvent.from_params(
            "ci38457511", "2019-07-06T03:19:53.040", 35.770, -117.599, 8.0, 7.1, "mw"
        ),
    ]
    filename = constants.TEST_DATA_DIR / "fdsn" / "events_info.txt"
    events = scalar_event.parse_events_file(filename=filename)
    assert EVENTS_DETAIL == events


def test_write_event_geojson():
    FILENAME = constants.TEST_DATA_DIR / "usp000hat0.geojson"
    with open(FILENAME, encoding="utf-8") as fin:
        data = json.load(fin)

    scratch_dir = constants.TEST_DATA_DIR / "scratch"
    scratch_dir.mkdir(exist_ok=True)
    scalar_event.write_event_geojson(data, scratch_dir)
    event_new = scalar_event.ScalarEvent.from_json(scratch_dir / "event.json")
    event = scalar_event.ScalarEvent.from_params(**EVENT_INFO)
    assert event_new == event
    shutil.rmtree(scratch_dir)
