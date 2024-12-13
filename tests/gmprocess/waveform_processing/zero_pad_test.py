import numpy as np
from gmprocess.waveform_processing.zero_pad import zero_pad


def test_zero_pad(load_data_us1000778i):
    streams, _ = load_data_us1000778i
    streams = streams.copy()
    stream = streams[0]
    pad_length = 0.5

    orig_npts = np.array([len(tr.data) for tr in stream])
    stream = zero_pad(stream, pad_length)
    new_npts = np.array([len(tr.data) for tr in stream])
    dt = stream[0].stats.delta
    assert np.all(new_npts - orig_npts == int(2 * pad_length / dt))
