import logging

import numpy as np

from gmprocess.core.streamcollection import StreamCollection
from gmprocess.io.read import read_data
from gmprocess.waveform_processing.processing import process_streams
from gmprocess.utils.logging import setup_logger
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.utils.config import get_config, update_dict, update_config
from gmprocess.utils.constants import TEST_DATA_DIR

CONFIG = get_config()

setup_logger()


def test_process_streams(geonet_uncorected_waveforms):
    # Loma Prieta test station (nc216859)
    # ???

    # data_files, event = read_data_dir("geonet", "us1000778i", "*.V1A")
    # streams = []
    # for f in data_files:
    #     streams += read_data(f)

    # Update default rather than loading static config
    # config = get_config()

    # update = {
    #     "processing": [
    #         {"snr_check": {"min_freq": 0.2}},
    #     ],
    #     # "sa": [
    #     #     {"periods": {"use_array": True, "defined_periods": 0.3}},
    #     # ]
    # }

    # update_dict(config, update)

    streams, event = geonet_uncorected_waveforms

    sc = StreamCollection(streams)

    sc.describe()

    config = update_config(str(TEST_DATA_DIR / "config_min_freq_0p2.yml"), CONFIG)

    test = process_streams(sc, event, config=config)

    logging.info(f"Testing trace: {test[0][1]}")

    assert len(test) == 3
    assert len(test[0]) == 3
    assert len(test[1]) == 3
    assert len(test[2]) == 3

    # Apparently the traces end up in a different order on the Travis linux
    # container than on my local mac. So testing individual traces need to
    # not care about trace order.

    trace_maxes = np.sort(
        [np.max(np.abs(t.data)) for t in test.select(station="HSES")[0]]
    )

    np.testing.assert_allclose(
        trace_maxes, np.array([157.81244924, 240.37952095, 263.6015194]), rtol=1e-5
    )

    # x: array([158.99, 239.48, 258.44])
    # y: array([157.812449, 240.379521, 263.601519])


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


def test_check_instrument(fdsn_nc51194936):
    config = get_config()

    # Update default rather than loading static config
    update = {
        "processing": [
            {"check_instrument": {"n_max": 3, "n_min": 1, "require_two_horiz": True}},
        ]
    }
    update_dict(config, update)

    streams, event = fdsn_nc51194936

    sc = StreamCollection(streams)
    sc.describe()

    test = process_streams(sc, event, config=config)

    for sta, expected in [("CVS", True), ("GASB", True), ("SBT", False)]:
        st = test.select(station=sta)[0]
        logging.info(f"Testing stream: {st}")
        assert st.passed == expected
