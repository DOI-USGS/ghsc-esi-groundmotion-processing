import pytest

from gmprocess.io.read import read_data
from gmprocess.utils.test_utils import read_data_dir


@pytest.fixture(scope="module")
def load_test_waveforms():
    data_files, _ = read_data_dir("geonet", "us1000778i", "20161113_110259_WTMC_20.V1A")
    streams = []
    for f in data_files:
        streams += read_data(f)

    yield streams
