from gmprocess.io.read_directory import directory_to_streams
from gmprocess.utils.logging import setup_logger
from gmprocess.utils.constants import TEST_DATA_DIR

setup_logger()


def test_directory_to_streams():
    directory = TEST_DATA_DIR / "read_directory" / "whittier87"

    streams, _, _ = directory_to_streams(directory)
    assert len(streams) == 7
