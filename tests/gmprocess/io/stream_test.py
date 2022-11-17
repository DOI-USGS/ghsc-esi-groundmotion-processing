#!/usr/bin/env python
# -*- coding: utf-8 -*-

# stdlib imports
import os

# third party imports
import numpy as np

# Local imports
from gmprocess.io.geonet.core import read_geonet
from gmprocess.io.knet.core import read_knet
from gmprocess.io.read import read_data
from gmprocess.io.stream import streams_to_dataframe
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.utils.test_utils import read_data_dir


def test():
    # Test for channel grouping with three unique channels
    streams = []
    # datadir = os.path.join(homedir, '..', 'data', 'knet', 'us2000cnnl')
    datafiles, _ = read_data_dir("knet", "us2000cnnl", "AOM0031801241951*")
    for datafile in datafiles:
        streams += read_knet(datafile)
    grouped_streams = StreamCollection(streams)
    assert len(grouped_streams) == 1
    assert grouped_streams[0].count() == 3

    # Test for channel grouping with more file types
    datafiles, _ = read_data_dir("geonet", "us1000778i", "20161113_110313_THZ_20.V2A")
    datafile = datafiles[0]
    streams += read_geonet(datafile)
    grouped_streams = StreamCollection(streams)
    assert len(grouped_streams) == 2
    assert grouped_streams[0].count() == 3
    assert grouped_streams[1].count() == 3

    # Test for warning for one channel streams
    datafiles, _ = read_data_dir("knet", "us2000cnnl", "AOM0071801241951.UD")
    datafile = datafiles[0]
    streams += read_knet(datafile)

    grouped_streams = StreamCollection(streams)
    #    assert "One channel stream:" in logstream.getvalue()

    assert len(grouped_streams) == 3
    assert grouped_streams[0].count() == 3
    assert grouped_streams[1].count() == 3
    assert grouped_streams[2].count() == 1


def test_grouping():
    cwb_files, _ = read_data_dir("cwb", "us1000chhc")
    cwb_streams = []
    for filename in cwb_files:
        cwb_streams += read_data(filename)
    cwb_streams = StreamCollection(cwb_streams)
    assert len(cwb_streams) == 5
    for stream in cwb_streams:
        assert len(stream) == 3

    # geonet
    geonet_files, _ = read_data_dir("geonet", "us1000778i", "*.V1A")
    geonet_streams = []
    for filename in geonet_files:
        geonet_streams += read_data(filename)
    geonet_streams = StreamCollection(geonet_streams)
    assert len(geonet_streams) == 3
    for stream in geonet_streams:
        assert len(stream) == 3
        assert len(stream.select(station=stream[0].stats.station)) == 3
        level = stream[0].stats.standard.process_level
        for trace in stream:
            assert trace.stats.standard.process_level == level

    # kiknet
    kiknet_files, _ = read_data_dir("kiknet", "usp000a1b0")
    kiknet_streams = []
    for filename in kiknet_files:
        kiknet_streams += read_data(filename)
    kiknet_streams = StreamCollection(kiknet_streams)
    assert len(kiknet_streams) == 1
    for stream in kiknet_streams:
        assert len(stream) == 3
        assert len(stream.select(station=stream[0].stats.station)) == 3

    # knet
    knet_files, _ = read_data_dir("knet", "us2000cnnl")
    knet_streams = []
    for filename in knet_files:
        knet_streams += read_data(filename)
    knet_streams = StreamCollection(knet_streams)
    assert len(knet_streams) == 9
    for stream in knet_streams:
        assert len(stream) == 3
        assert len(stream.select(station=stream[0].stats.station)) == 3
        pl = stream[0].stats.standard.process_level
        for trace in stream:
            assert trace.stats.standard.process_level == pl

    # smc
    smc_files, _ = read_data_dir("smc", "nc216859", "0111*")
    smc_streams = []
    for filename in smc_files:
        smc_streams += read_data(filename, any_structure=True)
    smc_streams = StreamCollection(smc_streams)
    assert len(smc_streams) == 1
    for stream in smc_streams:
        if stream[0].stats.station == "DVD0":
            assert len(stream) == 1
            assert len(stream.select(station=stream[0].stats.station)) == 1
        elif stream[0].stats.location == "01":
            assert len(stream) == 2
            assert len(stream.select(station=stream[0].stats.station)) == 2
        else:
            assert len(stream) == 3
            assert len(stream.select(station=stream[0].stats.station)) == 3

    # usc
    usc_files, _ = read_data_dir("usc", "ci3144585")
    usc_streams = []
    for filename in usc_files:
        if os.path.basename(filename) != "017m30bt.s0a":
            usc_streams += read_data(filename)
    usc_streams = StreamCollection(usc_streams)
    assert len(usc_streams) == 3
    for stream in usc_streams:
        if stream[0].stats.station == "57":
            assert len(stream) == 1
        else:
            assert len(stream) == 3


def test_to_dataframe():
    cwb_files, event = read_data_dir("geonet", "nz2018p115908")
    st = read_data(cwb_files[0])[0]
    df1 = streams_to_dataframe([st, st], event=event)
    np.testing.assert_array_equal(df1.STATION.tolist(), ["WPWS", "WPWS"])
    np.testing.assert_array_equal(
        df1.NAME.tolist(), ["Waipawa_District_Council", "Waipawa_District_Council"]
    )

    # let's use sets to make sure all the columns are present in whatever order
    cmp1 = set(
        [
            "ELEVATION",
            "EPICENTRAL_DISTANCE",
            "GC2_RX_DISTANCE",
            "GC2_RY0_DISTANCE",
            "GC2_RY_DISTANCE",
            "GC2_T_DISTANCE",
            "GC2_U_DISTANCE",
            "GREATER_OF_TWO_HORIZONTALS",
            "H1",
            "H2",
            "HYPOCENTRAL_DISTANCE",
            "JOYNER_BOORE_DISTANCE",
            "JOYNER_BOORE_VAR_DISTANCE",
            "LAT",
            "LON",
            "NAME",
            "NETID",
            "RUPTURE_DISTANCE",
            "RUPTURE_VAR_DISTANCE",
            "SOURCE",
            "STATION",
            "Z",
        ]
    )
    cmp2 = set(["", "PGA", "PGV", "SA(0.300)", "SA(1.000)", "SA(3.000)"])
    header1 = set(df1.columns.levels[0])
    header2 = set(df1.columns.levels[1])
    assert header1 == cmp1
    assert header2 == cmp2


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_grouping()
    test()
    test_to_dataframe()
