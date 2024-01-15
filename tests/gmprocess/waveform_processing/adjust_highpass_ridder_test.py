import numpy as np
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.io.read import read_data
from gmprocess.utils.tests_utils import read_data_dir
from gmprocess.waveform_processing.adjust_highpass_ridder import ridder_fchp
from gmprocess.utils.config import get_config


def test_auto_fchp(geonet_WTMC_uncorrected):
    # Use just the stream for the WTMC station V1A file
    streams, _ = geonet_WTMC_uncorrected

    # Shorten window for testing
    for tr in streams[0]:
        tr.data = tr.data[7000:18000]

    sc = StreamCollection(streams)
    output_fchp = []

    config = get_config()

    for st in sc:
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
            config=config,
        )
        for tr in tmp_st:
            initial_corners = tr.get_parameter("corner_frequencies")
            output_fchp.append(initial_corners["highpass"])

    target_fchp = np.array(
        [0.20188389843757404, 0.19428991918682328, 0.2558813590181579]
    )

    np.testing.assert_allclose(output_fchp, target_fchp, atol=1e-7)
