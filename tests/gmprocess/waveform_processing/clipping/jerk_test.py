import numpy as np
from gmprocess.io.read import read_data
from gmprocess.utils.tests_utils import read_data_dir
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.waveform_processing.clipping.jerk import Jerk


def test_num_outliers():
    data_files, _ = read_data_dir("clipping_samples", "hv70907436", "*.mseed")
    data_files.sort()
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)

    num_outliers = []
    for st in sc:
        jerk_method = Jerk(st)
        num_outliers.append(jerk_method.num_outliers)

    np.testing.assert_equal(num_outliers, np.array([765, 414, 733, 556, 926, 793]))


def test_all_num_outliers():
    data_files, _ = read_data_dir("clipping_samples", "hv70907436", "*.mseed")
    data_files.sort()
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)

    num_outliers = []
    for st in sc:
        jerk_method = Jerk(st, test_all=True)
        num_outliers.append(jerk_method.num_outliers)

    np.testing.assert_equal(
        num_outliers,
        np.array(
            [
                [765, 468, 689],
                [414, 677, 852],
                [733, 535, 1119],
                [556, 678, 712],
                [926, 996, 817],
                [793, 1017, 1567],
            ]
        ),
    )
