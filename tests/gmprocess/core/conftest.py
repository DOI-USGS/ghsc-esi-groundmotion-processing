"""Module to define fixutres for the core package."""

import pytest

from gmprocess.core.streamcollection import StreamCollection
from gmprocess.utils.constants import TEST_DATA_DIR


@pytest.fixture(scope="package")
def load_data_uw61251926():
    ddir = TEST_DATA_DIR / "fdsn" / "uw61251926" / "strong_motion"
    return StreamCollection.from_directory(ddir)
