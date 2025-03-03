import numpy as np
from obspy import UTCDateTime

from gmprocess.core.streamcollection import StreamCollection
from gmprocess.waveform_processing.processing import process_streams
from gmprocess.utils.config import update_dict
from gmprocess.utils import constants
from gmprocess.core import scalar_event


def test_zero_crossings(config):

    datadir = constants.TEST_DATA_DIR / "zero_crossings"
    sc = StreamCollection.from_directory(str(datadir))
    sc.describe()

    update = {
        "processing": [
            {"detrend": {"detrending_method": "demean"}},
            {"check_zero_crossings": {"min_crossings": 1}},
        ]
    }
    update_dict(config, update)

    edict = {
        "id": "ak20419010",
        "time": UTCDateTime("2018-11-30T17:29:29"),
        "latitude": 61.346,
        "longitude": -149.955,
        "depth_km": 46.7,
        "magnitude": 7.1,
    }
    event = scalar_event.ScalarEvent.from_params(**edict)
    test = process_streams(sc, event, config)
    for st in test:
        for tr in st:
            assert tr.has_parameter("ZeroCrossingRate")
    np.testing.assert_allclose(
        test[0][0].get_parameter("ZeroCrossingRate")["crossing_rate"],
        0.008888888888888889,
        atol=1e-5,
    )
