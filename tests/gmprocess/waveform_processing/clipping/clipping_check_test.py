import numpy as np
import obspy

from gmprocess.io.read import read_data
from gmprocess.core.stationstream import StationStream
from gmprocess.waveform_processing.clipping.clipping_check import check_clipping
from gmprocess.core import scalar_event
from gmprocess.utils import constants
from gmprocess.utils import tests_utils


def test_check_clipping():
    data_files, event = tests_utils.read_data_dir(
        "clipping_samples", "hv70907436", "*.mseed"
    )
    data_files.sort()
    streams = []
    for f in data_files:
        streams += read_data(f)

    codes = ["HV.TOUO", "HV.MOKD", "HV.MLOD", "HV.HOVE", "HV.HUAD", "HV.HSSD"]
    passed = []
    for code in codes:
        traces = []
        for ss in streams:
            tcode = f"{ss[0].stats.network}.{ss[0].stats.station}"
            if tcode == code:
                traces.append(ss[0])
        st = StationStream(traces)
        check_clipping(st, event)
        passed.append(st.passed)

    assert np.all(~np.array(passed))


def test_check_clipping_turkey():
    STATION = "KO.KIZT"
    data_dir = constants.TEST_DATA_DIR / "clipping_samples" / "us6000jlqa"
    inventory = obspy.read_inventory(data_dir / f"{STATION}.xml")
    traces = obspy.read(data_dir / f"{STATION}*.mseed")
    station_stream = StationStream(traces, inventory)

    event = scalar_event.ScalarEvent.from_json(data_dir / constants.EVENT_FILE)

    check_clipping(station_stream, event)
    passed = [st.passed for st in station_stream]
    assert np.all(~np.array(passed))
