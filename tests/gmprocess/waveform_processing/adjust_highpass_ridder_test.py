import copy

import numpy as np

from gmprocess.waveform_processing.adjust_highpass_ridder import ridder_fchp


def test_auto_fchp(load_data_us1000778i, config):
    conf = copy.deepcopy(config)
    streams, _ = load_data_us1000778i
    streams = streams.copy()

    # Shorten window for testing
    for tr in streams[0]:
        tr.data = tr.data[7000:18000]

    output_fchp = []
    for st in streams:
        for tr in st:
            tr.set_parameter(
                "corner_frequencies",
                {"type": "constant", "highpass": 0.001, "lowpass": 20},
            )

        tmp_st = ridder_fchp(
            st,
            target=0.008,
            tol=0.001,
            maxiter=30,
            maxfc=0.5,
            config=conf,
        )
        for tr in tmp_st:
            initial_corners = tr.get_parameter("corner_frequencies")
            output_fchp.append(initial_corners["highpass"])

    target_fchp = np.array([0.38825791309377045, 0.379440012761742, 0.001])
    np.testing.assert_allclose(output_fchp, target_fchp, atol=1e-7)
