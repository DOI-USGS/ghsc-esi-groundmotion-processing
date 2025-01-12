import numpy as np
from gmprocess.waveform_processing.zero_pad import zero_pad, strip_zero_pad


def test_zero_pad(load_data_us1000778i, config):
    streams, _ = load_data_us1000778i
    streams = streams.copy()
    stream = streams[0]
    pad_length = 0.5
    orig_npts = np.array([len(tr.data) for tr in stream])

    stream = zero_pad(stream, pad_length)

    new_npts = np.array([len(tr.data) for tr in stream])
    dt = stream[0].stats.delta
    assert np.all(new_npts - orig_npts == int(2 * pad_length / dt))

    # Reset the stream
    streams, _ = load_data_us1000778i
    streams = streams.copy()
    stream = streams[0]

    # To test the fhp method, need to have corner frequencies set
    freq_dict = {"lowpass": 20.0, "highpass": 0.039}
    for trace in stream:
        trace.set_parameter("corner_frequencies", freq_dict)

    stream = zero_pad(stream, length="fhp", config=config)

    new_npts = np.array([len(tr.data) for tr in stream])
    test_length = 1.5 * 5 / freq_dict["highpass"]
    assert np.all(new_npts - orig_npts == int(test_length / dt + 1))

    # Strip pads
    stream = strip_zero_pad(stream)
    new_npts = np.array([len(tr.data) for tr in stream])
    assert np.all(new_npts == orig_npts)
