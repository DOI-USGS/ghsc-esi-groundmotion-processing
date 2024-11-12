import os.path
import numpy as np

from gmprocess.io.geonet.core import is_geonet


def test_geonet(load_data_us1000778i):
    streams, _ = load_data_us1000778i
    streams = streams.copy()

    # test a non-geonet file
    assert is_geonet(os.path.abspath(__file__)) is False

    pgas = []
    for st in streams:
        for tr in st:
            pgas.append(np.abs(tr.data).max())

    target = np.array([158.99, 239.48, 258.44])
    np.testing.assert_allclose(target, np.sort(pgas))
