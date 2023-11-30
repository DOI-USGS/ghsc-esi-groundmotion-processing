# third party imports
import numpy as np

# local imports
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.io.read import read_data
from gmprocess.waveform_processing.processing import process_streams
from gmprocess.utils.logging import setup_logger
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.utils.config import get_config, update_dict

setup_logger()


def test_nnet(geonet_WTMC_uncorrected):
    conf = get_config()

    update = {
        "processing": [
            {"detrend": {"detrending_method": "demean"}},
            {"detrend": {"detrending_method": "linear"}},
            {"compute_snr": {"bandwidth": 20.0}},
            {"snr_check": {"max_freq": 5.0, "min_freq": 0.2, "threshold": 3.0}},
            {"nnet_qa": {"acceptance_threshold": 0.5, "model_name": "CantWell"}},
        ]
    }
    update_dict(conf, update)

    streams, event = geonet_WTMC_uncorrected

    sc = StreamCollection(streams)
    test = process_streams(sc, event, conf)
    nnet_dict = test[0].get_stream_param("nnet_qa")
    np.testing.assert_allclose(nnet_dict["score_HQ"], 0.9996686646819085, rtol=1e-3)

    # For station WTMC (uncorrected)
    # np.testing.assert_allclose(nnet_dict["score_HQ"], 0.9992308897749704, rtol=1e-5)
