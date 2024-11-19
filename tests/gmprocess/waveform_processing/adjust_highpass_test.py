import numpy as np

from gmprocess.waveform_processing.adjust_highpass import adjust_highpass_corner


def test_adjust_highpass_corner(load_data_us1000778i):
    streams, _ = load_data_us1000778i
    streams = streams.copy()

    # Shorten window for testing
    for tr in streams[0]:
        tr.data = tr.data[6000:20000]

    output_fchp = []

    for st in streams:
        for tr in st:
            tr.set_parameter(
                "corner_frequencies",
                {"type": "constant", "highpass": 0.01, "lowpass": 20},
            )

        tmp_st = adjust_highpass_corner(
            st, max_final_displacement=0.0001, max_displacement_ratio=0.001
        )
        for tr in tmp_st:
            initial_corners = tr.get_parameter("corner_frequencies")
            output_fchp.append(initial_corners["highpass"])
    target_fchp = np.array([0.3844335937500001, 0.3844335937500001, 0.3844335937500001])

    np.testing.assert_allclose(output_fchp, target_fchp, atol=1e-7)
