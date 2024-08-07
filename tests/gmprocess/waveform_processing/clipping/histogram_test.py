import numpy as np
from gmprocess.io.read import read_data
from gmprocess.utils.tests_utils import read_data_dir
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.waveform_processing.clipping.histogram import Histogram


def test_num_clip_intervals():
    data_files, _ = read_data_dir("clipping_samples", "hv70907436", "*.mseed")
    data_files.sort()
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)

    num_clip_intervals = []
    for st in sc:
        hist_method = Histogram(st)
        num_clip_intervals.append(hist_method.num_clip_intervals)

    np.testing.assert_equal(
        num_clip_intervals, [[0, 0, 0], [0, 1], [1], [1], [1], [0, 0, 1]]
    )


def test_all_num_clip_intervals():
    data_files, _ = read_data_dir("clipping_samples", "hv70907436", "*.mseed")
    data_files.sort()
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)

    num_clip_intervals = []
    for st in sc:
        hist_method = Histogram(st, test_all=True)
        num_clip_intervals.append(hist_method.num_clip_intervals)

    np.testing.assert_equal(
        num_clip_intervals,
        [[0, 0, 0], [0, 1, 1], [1, 2, 2], [1, 1, 0], [1, 1, 1], [0, 0, 1]],
    )
