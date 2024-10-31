import numpy as np

from gmprocess.waveform_processing.corner_frequencies import (
    get_corner_frequencies,
)


def test_corner_frequencies(setup_corner_freq_test):
    # Default config has 'constant' corner frequency method, so the need
    # here is to force the 'snr' method.
    _, event, processed_streams = setup_corner_freq_test

    lp = []
    hp = []
    for stream in processed_streams:
        if not stream.passed:
            continue
        stream = get_corner_frequencies(stream, event, method="snr")
        if stream[0].has_parameter("corner_frequencies"):
            cfdict = stream[0].get_parameter("corner_frequencies")
            lp.append(cfdict["lowpass"])
            hp.append(cfdict["highpass"])
    np.testing.assert_allclose(
        np.sort(hp), [0.02491901, 0.02498751, 0.02577984], atol=1e-5
    )

    st = processed_streams.select(station="THZ")[0]
    lps = [tr.get_parameter("corner_frequencies")["lowpass"] for tr in st]
    hps = [tr.get_parameter("corner_frequencies")["highpass"] for tr in st]
    np.testing.assert_allclose(np.sort(lps), [50.0, 50.0, 100.0], atol=1e-6)
    np.testing.assert_allclose(
        np.sort(hps), [0.02498751, 0.02498751, 0.02498751], atol=1e-5
    )

    lp = []
    hp = []
    for stream in processed_streams:
        if not stream.passed:
            continue
        stream = get_corner_frequencies(stream, event, method="snr")
        if stream[0].has_parameter("corner_frequencies"):
            cfdict = stream[0].get_parameter("corner_frequencies")
            lp.append(cfdict["lowpass"])
            hp.append(cfdict["highpass"])

    np.testing.assert_allclose(
        np.sort(hp), [0.02491901, 0.02498751, 0.02577984], atol=1e-5
    )

    st = processed_streams.select(station="HSES")[0]
    lps = [tr.get_parameter("corner_frequencies")["lowpass"] for tr in st]
    hps = [tr.get_parameter("corner_frequencies")["highpass"] for tr in st]

    np.testing.assert_allclose(np.sort(lps), [100.0, 100.0, 100.0], atol=1e-6)
    np.testing.assert_allclose(
        np.sort(hps), [0.02491901, 0.02491901, 0.02491901], atol=1e-5
    )


def test_corner_frequencies_magnitude(setup_corner_freq_mag_test):
    # Default config has 'constant' corner frequency method, so the need
    # here is to force the 'magnitude' method.

    _, event, processed_streams = setup_corner_freq_mag_test

    lp = []
    hp = []
    for stream in processed_streams:
        if not stream.passed:
            continue
        stream = get_corner_frequencies(stream, event, method="magnitude")
        if stream[0].has_parameter("corner_frequencies"):
            cfdict = stream[0].get_parameter("corner_frequencies")
            lp.append(cfdict["lowpass"])
            hp.append(cfdict["highpass"])

    print(hp)
    np.testing.assert_allclose(hp, [0.3])
    np.testing.assert_allclose(lp, [35.0])
