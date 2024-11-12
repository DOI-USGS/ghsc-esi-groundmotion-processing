import numpy as np

from gmprocess.metrics.oscillator import calculate_spectrals


def test_spectral(load_data_us1000778i):
    streams, _ = load_data_us1000778i
    streams = streams.copy()

    acc = streams[0][0]
    osc = calculate_spectrals(acc, 1.0, 0.05)[0]
    np.testing.assert_allclose(np.max(np.abs(osc)), 413.211428)
