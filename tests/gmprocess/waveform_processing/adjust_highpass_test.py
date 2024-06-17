import numpy as np

from gmprocess.core.streamcollection import StreamCollection
from gmprocess.waveform_processing.adjust_highpass import adjust_highpass_corner


def test_adjust_highpass_corner(geonet_WTMC_uncorrected):
    # Use just the stream for the WTMC station V1A file
    streams, _ = geonet_WTMC_uncorrected

    # Shorten window for testing
    for tr in streams[0]:
        tr.data = tr.data[7000:18000]

    sc = StreamCollection(streams)
    output_fchp = []

    for st in sc:
        for tr in st:
            tr.set_parameter(
                "corner_frequencies",
                {"type": "constant", "highpass": 0.001, "lowpass": 20},
            )

        tmp_st = adjust_highpass_corner(
            st, max_final_displacement=0.02, max_displacement_ratio=0.1
        )
        for tr in tmp_st:
            initial_corners = tr.get_parameter("corner_frequencies")
            output_fchp.append(initial_corners["highpass"])

    target_fchp = np.array([0.129746337890625, 0.001, 0.001])

    np.testing.assert_allclose(output_fchp, target_fchp, atol=1e-7)
