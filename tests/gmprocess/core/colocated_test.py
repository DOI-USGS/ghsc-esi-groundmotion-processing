from gmprocess.core.streamcollection import StreamCollection
from gmprocess.utils.constants import TEST_DATA_DIR


def test_colocated():
    datadir = TEST_DATA_DIR / "colocated_instruments"
    sc = StreamCollection.from_directory(datadir)

    sc.select_colocated()
    assert sc.n_passed == 7
    assert sc.n_failed == 4

    # What if no preference is matched?
    sc = StreamCollection.from_directory(datadir)
    sc.select_colocated(preference=["XX"])
    assert sc.n_passed == 3
    assert sc.n_failed == 8
