import numpy as np

from gmprocess.io.read import read_data
from gmprocess.metrics.oscillator import calculate_spectrals
from gmprocess.utils.tests_utils import read_data_dir


def test_spectral():
    datafiles, _ = read_data_dir("geonet", "us1000778i", "20161113_110259_WTMC_20.V2A")
    acc_file = datafiles[0]
    acc = read_data(acc_file)[0][0]
    osc = calculate_spectrals(acc, 1.0, 0.05)[0]
    np.testing.assert_allclose(np.max(np.abs(osc)), 1336.1601016028935)
