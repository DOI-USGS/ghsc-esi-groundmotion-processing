import copy

import numpy as np
from obspy import UTCDateTime

from gmprocess.core.streamcollection import StreamCollection
from gmprocess.waveform_processing.processing import process_streams
from gmprocess.utils.config import update_dict
from gmprocess.core import scalar_event
from gmprocess.utils import constants


def test_lowpass_max(config):
    conf = copy.deepcopy(config)

    datadir = constants.TEST_DATA_DIR / "lowpass_max"
    sc = StreamCollection.from_directory(datadir)

    update = {
        "processing": [
            {"detrend": {"detrending_method": "demean"}},
            {
                "remove_response": {
                    "pre_filt": True,
                    "f1": 0.001,
                    "f2": 0.005,
                    "f3": None,
                    "f4": None,
                    "water_level": 60,
                }
            },
            {
                "get_corner_frequencies": {
                    "constant": {"highpass": 0.08, "lowpass": 20.0},
                    "method": "constant",
                    "snr": {"same_horiz": True},
                }
            },
            {"lowpass_max_frequency": {"fn_fac": 0.9}},
        ]
    }
    update_dict(conf, update)
    update = {
        "windows": {
            "signal_end": {
                "method": "model",
                "vmin": 1.0,
                "floor": 120,
                "model": "AS16",
                "epsilon": 2.0,
            },
            "window_checks": {
                "enabled": False,
                "min_noise_duration": 1.0,
                "min_signal_duration": 1.0,
            },
        }
    }
    update_dict(conf, update)
    event_values = {
        "id": "ci38038071",
        "time": UTCDateTime("2018-08-30 02:35:36"),
        "latitude": 34.136,
        "longitude": -117.775,
        "depth_km": 5.5,
        "magnitude": 4.4,
    }
    event = scalar_event.ScalarEvent.from_params(**event_values)
    test = process_streams(sc, event, conf)
    for st in test:
        for tr in st:
            freq_dict = tr.get_parameter("corner_frequencies")
            np.testing.assert_allclose(freq_dict["lowpass"], 18.0)
