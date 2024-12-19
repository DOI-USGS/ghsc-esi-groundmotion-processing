import copy

import numpy as np

from gmprocess.core.streamcollection import StreamCollection
from gmprocess.io.obspy.core import read_obspy
from gmprocess.utils.tests_utils import read_data_dir
from gmprocess.waveform_processing.processing import process_streams

from obspy import read


def test_sac_conversion(config):
    conf = copy.deepcopy(config)
    # The "sac_conversion_factor" is specified in the "read" section of the config.
    # It is a multiplicative factor to convert from whatever units the data is in to
    # cm/s/s. This test is for how that conversion factor is applied.

    # We will use a CSN data file
    datafiles, _ = read_data_dir("csn", "ci38457511", "*.sac")
    datafiles.sort()
    datafile = datafiles[0]

    # First, read in with obspy, which reads in the raw data:
    tr_obspy = read(datafile)[0]
    pga_obspy = np.max(np.abs(tr_obspy.data))

    # Read in with gmprocess, which applies the conversion factor, specifying the
    # conversion factor
    conf["read"]["sac_conversion_factor"] = 980.665
    tr_gmprocess = read_obspy(datafile, config=conf)[0][0]
    pga_gmprocess = np.max(np.abs(tr_gmprocess))
    np.testing.assert_allclose(pga_gmprocess, pga_obspy * 980.665)


def test_sac_csn(config):
    conf = copy.deepcopy(config)
    # This reads in example SAC data that does not have a separate metadata
    # file to meet the needs of the Community Seismic Network:
    # http://csn.caltech.edu/
    conf["read"]["sac_conversion_factor"] = 980.665

    datafiles, _ = read_data_dir("csn", "ci38457511", "*.sac")
    datafiles.sort()
    traces = []
    for d in datafiles:
        traces.append(read_obspy(d, config=conf)[0][0])

    tr_amax = np.zeros(len(traces))
    for i, tr in enumerate(traces):
        tr_amax[i] = np.max(np.abs(tr.data))

    target_amax = np.array([42.54516983, 33.5615921, 992.60430908])
    np.testing.assert_allclose(target_amax, tr_amax)


def test_channel_exclusion():
    exclude_patterns = ["*.*.??.???"]
    datafiles, _ = read_data_dir("fdsn", "se60247871", "US.LRAL*.mseed")
    streams = []
    for datafile in datafiles:
        tstreams = read_obspy(datafile, exclude_patterns=exclude_patterns)
        if tstreams is None:
            continue
        else:
            streams += tstreams
    assert len(streams) == 0

    exclude_patterns = ["*.*.??.LN?"]
    datafiles, _ = read_data_dir("fdsn", "se60247871", "US.LRAL*.mseed")
    streams = []
    for datafile in datafiles:
        tstreams = read_obspy(datafile, exclude_patterns=exclude_patterns)
        if tstreams is None:
            continue
        else:
            streams += tstreams
    assert len(streams) == 0

    exclude_patterns = ["*.*.??.LN?"]
    datafiles, _ = read_data_dir("fdsn", "nc72282711", "BK.CMB*.mseed")
    streams = []
    for datafile in datafiles:
        tstreams = read_obspy(datafile, exclude_patterns=exclude_patterns)
        if tstreams is None:
            continue
        else:
            streams += tstreams
    assert len(streams) == 3

    exclude_patterns = ["*.*.??.[BH]NZ"]
    datafiles, _ = read_data_dir("fdsn", "ci38445975", "CI.MIKB*.mseed")
    streams = []
    for datafile in datafiles:
        tstreams = read_obspy(datafile, exclude_patterns=exclude_patterns)
        if tstreams is None:
            continue
        else:
            streams += tstreams
    assert len(streams) == 4

    exclude_patterns = ["US.*.??.???"]
    datafiles, _ = read_data_dir("fdsn", "se60247871", "US.LRAL*.mseed")
    streams = []
    for datafile in datafiles:
        tstreams = read_obspy(datafile, exclude_patterns=exclude_patterns)
        if tstreams is None:
            continue
        else:
            streams += tstreams
    assert len(streams) == 0

    exclude_patterns = ["*.LRAL.??.???"]
    datafiles, _ = read_data_dir("fdsn", "se60247871", "US.LRAL*.mseed")
    streams = []
    for datafile in datafiles:
        tstreams = read_obspy(datafile, exclude_patterns=exclude_patterns)
        if tstreams is None:
            continue
        else:
            streams += tstreams
    assert len(streams) == 0

    exclude_patterns = ["*.*.40.???"]
    datafiles, _ = read_data_dir("fdsn", "nc73300395", "BK.VALB*.mseed")
    streams = []
    for datafile in datafiles:
        tstreams = read_obspy(datafile, exclude_patterns=exclude_patterns)
        if tstreams is None:
            continue
        else:
            streams += tstreams
    assert len(streams) == 0

    exclude_patterns = ["US.LRAL.20.LNZ"]
    datafiles, _ = read_data_dir("fdsn", "se60247871", "US.LRAL*.mseed")
    streams = []
    for datafile in datafiles:
        tstreams = read_obspy(datafile, exclude_patterns=exclude_patterns)
        if tstreams is None:
            continue
        else:
            streams += tstreams
    assert len(streams) == 2

    exclude_patterns = ["*.*.??.BN?", "*.*.??.HN?"]
    datafiles, _ = read_data_dir("fdsn", "ci38445975", "CI.MIKB*.mseed")
    streams = []
    for datafile in datafiles:
        tstreams = read_obspy(datafile, exclude_patterns=exclude_patterns)
        if tstreams is None:
            continue
        else:
            streams += tstreams
    assert len(streams) == 0


def _test_weird_sensitivity():
    # Temporarily turn this off because the problem is that the units are wrong and so
    # we should turn it back on once we add code for dealing with unusual units.
    datafiles, event = read_data_dir("fdsn", "us70008dx7", "SL.KOGS*.mseed")
    streams = []
    for datafile in datafiles:
        streams += read_obspy(datafile)
    sc = StreamCollection(streams)
    psc = process_streams(sc, event)
    channel = psc[0].select(component="E")[0]
    np.testing.assert_allclose(channel.data.max(), 6.332352e-05)


def test():
    datafiles, _ = read_data_dir("fdsn", "nc72282711", "BK.CMB*.mseed")
    streams = []
    for datafile in datafiles:
        streams += read_obspy(datafile)

    assert streams[0].get_id() == "BK.CMB.HN"

    datafiles, _ = read_data_dir("fdsn", "nc72282711", "TA.M04C*.mseed")
    streams = []
    for datafile in datafiles:
        streams += read_obspy(datafile)

    assert streams[0].get_id() == "TA.M04C.HN"

    # test assignment of Z channel
    datafiles, _ = read_data_dir("fdsn", "nc73300395", "BK.VALB*.mseed")
    streams = []
    for datafile in datafiles:
        streams += read_obspy(datafile)

    # get all channel names
    channels = sorted([st[0].stats.channel for st in streams])
    assert channels == ["HN2", "HN3", "HNZ"]


if __name__ == "__main__":
    test_channel_exclusion()
