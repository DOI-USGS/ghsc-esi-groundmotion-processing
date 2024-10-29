import numpy as np
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.waveform_processing.baseline_correction import correct_baseline
from gmprocess.utils.config import get_config


def test_correct_baseline(geonet_uncorrected_waveforms):
    streams, _ = geonet_uncorrected_waveforms

    sc = StreamCollection(streams)
    final_acc = []

    config = get_config()
    config["integration"]["frequency"] = True

    for st in sc:
        for tr in st:
            tmp_tr = correct_baseline(tr, config=config)
            final_acc.append(tmp_tr.data[-1])

    target_final_acc = np.array(
        [
            9.178010e-01,
            3.992102e-01,
            -1.402800e00,
            3.778422e-01,
            -6.819437e-01,
            1.131405e-01,
            3.959804e-02,
            -1.160693e-03,
            -1.537016e-02,
        ]
    )

    np.testing.assert_allclose(final_acc, target_final_acc, atol=1e-6)
