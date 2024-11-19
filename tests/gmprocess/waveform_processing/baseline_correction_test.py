import copy

import numpy as np

from gmprocess.waveform_processing.baseline_correction import correct_baseline


def test_correct_baseline(load_data_us1000778i, config):
    conf = copy.deepcopy(config)
    streams, _ = load_data_us1000778i
    streams = streams.copy()

    final_acc = []
    conf["integration"]["frequency"] = True

    for st in streams:
        for tr in st:
            tmp_tr = correct_baseline(tr, config=conf)
            final_acc.append(tmp_tr.data[-1])

    target_final_acc = np.array(
        [0.37761623637200725, -0.6856875633042886, 0.11214700766157523]
    )

    np.testing.assert_allclose(final_acc, target_final_acc, atol=1e-6)
