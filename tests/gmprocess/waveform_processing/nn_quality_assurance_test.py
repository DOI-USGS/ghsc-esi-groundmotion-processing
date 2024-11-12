import copy

# third party imports
import numpy as np

# local imports
from gmprocess.waveform_processing.processing import process_streams
from gmprocess.utils.config import update_dict


def test_nnet(load_data_us1000778i, config):
    conf = copy.deepcopy(config)
    streams, event = load_data_us1000778i
    streams = streams.copy()

    update = {
        "processing": [
            {"detrend": {"detrending_method": "demean"}},
            {"detrend": {"detrending_method": "linear"}},
            {"compute_snr": {"smoothing_parameter": 20.0}},
            {"snr_check": {"max_freq": 5.0, "min_freq": 0.2, "threshold": 3.0}},
            {
                "nnet_qa": {
                    "acceptance_threshold": 0.5,
                    "model_name": "CantWell",
                }
            },
        ]
    }
    update_dict(conf, update)
    test = process_streams(streams, event, conf)
    nnet_dict = test[0].get_stream_param("nnet_qa")
    np.testing.assert_allclose(nnet_dict["score_HQ"], 0.999692659619901, rtol=1e-4)
