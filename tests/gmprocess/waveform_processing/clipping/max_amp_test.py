import numpy as np
from gmprocess.io.read import read_data
from gmprocess.utils.tests_utils import read_data_dir
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.waveform_processing.clipping.max_amp import MaxAmp


def test_max_calc():
    data_files, _ = read_data_dir("clipping_samples", "hv70907436", "*.mseed")
    data_files.sort()
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)

    st_max_amps = []
    for st in sc:
        max_amp_method = MaxAmp(st)
        st_max_amps.append(max_amp_method.max_amp)

    np.testing.assert_allclose(
        st_max_amps,
        np.array(
            [
                8602603.806491164,
                8397343.5183308,
                8118061.843255052,
                8804782.326482268,
                8509165.221988602,
                8919976.8097822,
            ]
        ),
        rtol=1e-5,
    )


def test_all_max_calc():
    data_files, _ = read_data_dir("clipping_samples", "hv70907436", "*.mseed")
    data_files.sort()
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)

    st_max_amps = []
    for st in sc:
        max_amp_method = MaxAmp(st, test_all=True)
        st_max_amps.append(max_amp_method.max_amp)

    np.testing.assert_allclose(
        st_max_amps,
        np.array(
            [
                [8602603.806491164, 5624495.914613594, 8340128.382967799],
                [8397343.5183308, 10509708.33107507, 8504667.111277295],
                [8118061.843255052, 8180193.2097507445, 8974185.416593455],
                [8804782.326482268, 8464344.46214153, 8195225.312664042],
                [8509165.221988602, 10519684.437012028, 8911500.583995689],
                [8919976.8097822, 8532867.24817831, 11425705.883105664],
            ]
        ),
        rtol=1e-5,
    )
