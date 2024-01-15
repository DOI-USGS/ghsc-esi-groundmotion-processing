import os.path
import numpy as np
from gmprocess.io.esm.core import is_esm, read_esm
from gmprocess.utils.tests_utils import read_data_dir
from gmprocess.utils.constants import TEST_DATA_DIR


def test():
    datadir = TEST_DATA_DIR / "esm"

    esm_file1 = str(datadir / "us60004wsq" / "HI.ARS1..HNE.D.20190728.160908.C.ACC.ASC")
    esm_file2 = str(datadir / "us60004wsq" / "HI.ARS1..HNN.D.20190728.160908.C.ACC.ASC")
    esm_file3 = str(datadir / "us60004wsq" / "HI.ARS1..HNZ.D.20190728.160908.C.ACC.ASC")
    esm_file4 = str(datadir / "usp000hpnf" / "20101114230825_3104_ap_RawAcc_E.asc")
    assert is_esm(esm_file1)
    assert is_esm(esm_file2)
    assert is_esm(esm_file3)
    assert is_esm(esm_file4)
    try:
        assert is_esm(os.path.abspath(__file__))
    except AssertionError:
        pass

    # test a esm file with npoints % 10 == 0
    stream1 = read_esm(esm_file1)[0]
    stream2 = read_esm(esm_file2)[0]
    stream3 = read_esm(esm_file3)[0]
    stream4 = read_esm(esm_file4)[0]
    np.testing.assert_almost_equal(stream1[0].max(), 0.300022, decimal=2)
    np.testing.assert_almost_equal(stream2[0].max(), 0.359017, decimal=2)
    np.testing.assert_almost_equal(stream3[0].max(), 0.202093, decimal=2)
    np.testing.assert_almost_equal(stream4[0].max(), 1.631975, decimal=2)

    # test that a file that is not esm format raises an Exception
    try:
        esm_files, _ = read_data_dir(
            "geonet", "nz2018p115908", "20161113_110256_WTMC_20.V1A"
        )

        esm_file = esm_files[0]
        read_esm(esm_file)[0]
        success = True
    except Exception:
        success = False
    assert not success
