import copy

import numpy as np

from gmprocess.core.streamcollection import StreamCollection
from gmprocess.waveform_processing.processing import process_streams
from gmprocess.utils.config import update_dict, update_config
from gmprocess.utils.constants import TEST_DATA_DIR


def test_process_streams(load_data_us1000778i, config):
    conf = copy.deepcopy(config)
    sc, event = load_data_us1000778i
    sc = sc.copy()

    update = {
        "processing": [
            {"detrend": {"detrending_method": "linear"}},
            {"detrend": {"detrending_method": "demean"}},
            {
                "remove_response": {
                    "pre_filt": "True",
                    "f1": 0.001,
                    "f2": 0.005,
                    "f3": None,
                    "f4": None,
                    "water_level": 60.0,
                }
            },
            {"detrend": {"detrending_method": "linear"}},
            {"detrend": {"detrending_method": "demean"}},
            {"compute_snr": {"smoothing_parameter": 20.0}},
            {
                "snr_check": {
                    "threshold": 3.0,
                    "min_freq": 0.2,
                    "max_freq": 5.0,
                    "f0_options": {
                        "stress_drop": 10,
                        "shear_vel": 3.7,
                        "ceiling": 2.0,
                    },
                }
            },
            {
                "get_corner_frequencies": {
                    "method": "constant",
                    "constant": {"highpass": 0.08, "lowpass": 20.0},
                    "magnitude": {
                        "minmag": [-999.0, 3.5, 5.5],
                        "highpass": [0.5, 0.3, 0.1],
                        "lowpass": [25.0, 35.0, 40.0],
                    },
                    "snr": {"same_horz": "True"},
                }
            },
            {"cut": {"sec_before_split": 2.0}},
            {"taper": {"type": "hann", "width": 0.05, "side": "both"}},
        ],
    }
    update_dict(conf, update)

    conf = update_config(str(TEST_DATA_DIR / "config_min_freq_0p2.yml"), conf)

    sc.describe()

    test = process_streams(sc, event, config=conf)

    assert len(test) == 1
    assert len(test[0]) == 3

    trace_maxes = np.sort([np.max(np.abs(t.data)) for t in test[0]])

    np.testing.assert_allclose(
        trace_maxes,
        np.array([157.81244924, 240.37952095, 263.6015194]),
        rtol=1e-5,
    )


def test_free_field(kiknet_usp000hzq8):
    raw_streams, event = kiknet_usp000hzq8

    sc = StreamCollection(raw_streams)

    processed_streams = process_streams(sc, event)

    # all of these streams should have failed for different reasons
    npassed = np.sum([pstream.passed for pstream in processed_streams])
    assert npassed == 0
    for pstream in processed_streams:
        is_free = pstream[0].free_field
        reason = ""
        for trace in pstream:
            if not trace.passed:
                reason = trace.get_parameter("failure")["reason"]
                break
        if is_free:
            assert reason.startswith("SNR check")
        else:
            assert reason == "Failed free field sensor check."


def test_check_instrument(fdsn_nc51194936, config):
    conf = copy.deepcopy(config)
    streams, event = fdsn_nc51194936

    # Update default rather than loading static config
    update = {
        "processing": [
            {
                "check_instrument": {
                    "n_max": 3,
                    "n_min": 1,
                    "require_two_horiz": True,
                }
            },
        ]
    }
    update_dict(conf, update)
    sc = StreamCollection(streams)
    test = process_streams(sc, event, config=conf)
    for sta, expected in [("CVS", True), ("GASB", True), ("SBT", False)]:
        st = test.select(station=sta)[0]
        assert st.passed == expected
