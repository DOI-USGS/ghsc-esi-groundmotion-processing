#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import numpy as np
import pandas as pd
from gmprocess.core.stationtrace import StationTrace
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.io.read import read_data
from gmprocess.utils.config import get_config
from gmprocess.utils.constants import TEST_DATA_DIR
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.waveform_processing import phase
from obspy import UTCDateTime, read
from obspy.core.stream import Stream
from obspy.geodetics import locations2degrees
from obspy.taup import TauPyModel
from scipy.io import loadmat

CONFIG = get_config()


def test_baer():
    datadir = TEST_DATA_DIR / "process"
    # Testing a strong motion channel
    st = read(str(datadir / "ALCTENE.UW..sac"))
    ppick = phase.pick_baer(st, CONFIG["pickers"])
    target = np.array([20.740000000000002, 59.54533997798557])
    np.testing.assert_allclose(ppick, target)


def test_p_pick():
    datadir = TEST_DATA_DIR / "process"
    # Testing a strong motion channel
    tr = read(str(datadir / "ALCTENE.UW..sac"))[0]
    chosen_ppick = UTCDateTime("2001-02-28T18:54:47")
    ppick = phase.PowerPicker(tr)
    ptime = tr.times("utcdatetime")[0] + ppick
    assert (abs(chosen_ppick - ptime)) < 0.2

    # Testing a broadband channel
    tr = read(str(datadir / "HAWABHN.US..sac"))[0]
    chosen_ppick = UTCDateTime("2003-01-15T03:42:12.5")
    ppick = phase.PowerPicker(tr)
    ptime = tr.times("utcdatetime")[0] + ppick
    assert (abs(chosen_ppick - ptime)) < 0.2

    # Test a Northridge file that should fail to return a P-pick
    tr = read_data(datadir / "017m30ah.m0a")[0][0]
    ppick = phase.PowerPicker(tr)
    assert ppick == -1


def test_pphase_picker():
    # compare our results with a data file from E. Kalkan
    datafile = TEST_DATA_DIR / "strong-motion.mat"
    matlabfile = loadmat(str(datafile))
    x = np.squeeze(matlabfile["x"])

    dt = matlabfile["dt"][0][0]
    hdr = {
        "channel": "HN1",
        "delta": dt,
        "sampling_rate": 1 / dt,
        "npts": len(x),
        "starttime": UTCDateTime("1970-01-01"),
        "standard": {
            "corner_frequency": np.nan,
            "station_name": "",
            "source": "json",
            "instrument": "",
            "instrument_period": np.nan,
            "source_format": "json",
            "comments": "",
            "structure_type": "",
            "sensor_serial_number": "",
            "process_level": "raw counts",
            "process_time": "",
            "source_file": "",
            "horizontal_orientation": np.nan,
            "vertical_orientation": np.nan,
            "units": "cm/s/s",
            "units_type": "acc,",
            "instrument_sensitivity": np.nan,
            "volts_to_counts": np.nan,
            "instrument_damping": np.nan,
        },
    }
    trace = StationTrace(data=x, header=hdr)
    stream = Stream(traces=[trace])
    period = 0.01
    damping = 0.6
    nbins = 200
    loc = phase.pphase_pick(
        stream[0], period=period, damping=damping, nbins=nbins, peak_selection=True
    )
    print(loc)
    np.testing.assert_allclose(loc, 26.105)


def test_all_pickers():
    streams = get_streams()
    picker_config = CONFIG["pickers"]
    methods = ["ar", "baer", "power", "kalkan"]
    rows = []
    for stream in streams:
        print(stream.get_id())
        for method in methods:
            if method == "ar":
                loc, mean_snr = phase.pick_ar(stream, picker_config=picker_config)
            elif method == "baer":
                loc, mean_snr = phase.pick_baer(stream, picker_config=picker_config)
            elif method == "power":
                loc, mean_snr = phase.pick_power(stream, picker_config=picker_config)
            elif method == "kalkan":
                loc, mean_snr = phase.pick_kalkan(stream, picker_config=picker_config)
            elif method == "yeck":
                loc, mean_snr = phase.pick_yeck(stream)
            row = {
                "Stream": stream.get_id(),
                "Method": method,
                "Pick_Time": loc,
                "Mean_SNR": mean_snr,
            }
            rows.append(row)
    df = pd.DataFrame(rows)

    stations = df["Stream"].unique()
    cmpdict = {
        "NZ.HSES.HN": "baer",
        "NZ.WTMC.HN": "baer",
        "NZ.THZ.HN": "power",
    }
    for station in stations:
        station_df = df[df["Stream"] == station]
        max_snr = station_df["Mean_SNR"].max()
        maxrow = station_df[station_df["Mean_SNR"] == max_snr].iloc[0]
        method = maxrow["Method"]
        assert cmpdict[station] == method


def test_travel_time():
    datafiles, event = read_data_dir("geonet", "us1000778i", "*.V1A")
    streams = []
    for datafile in datafiles:
        streams += read_data(datafile)

    cmps = {
        "NZ.HSES.HN": 42.12651866051254,
        "NZ.WTMC.HN": 40.78674514049763,
        "NZ.THZ.HN": 42.016659723287404,
    }
    for stream in streams:
        minloc, _ = phase.pick_travel(stream, event)
        # print(stream, minloc)
        np.testing.assert_almost_equal(minloc, cmps[stream.get_id()], decimal=3)


def get_streams():
    datafiles3, _ = read_data_dir("geonet", "us1000778i", "*.V1A")
    datafiles = datafiles3
    streams = []
    for datafile in datafiles:
        streams += read_data(datafile)

    return StreamCollection(streams)


def test_get_travel_time_df():
    datadir = TEST_DATA_DIR / "travel_times"

    sc1 = StreamCollection.from_directory(str(datadir / "ci37218996"))
    sc2 = StreamCollection.from_directory(str(datadir / "ci38461735"))
    scs = [sc1, sc2]

    df1, catalog = phase.create_travel_time_dataframe(
        sc1, str(datadir / "catalog_test_traveltimes.csv"), 5, 0.1, "iasp91"
    )
    df2, catalog = phase.create_travel_time_dataframe(
        sc2, str(datadir / "catalog_test_traveltimes.csv"), 5, 0.1, "iasp91"
    )

    model = TauPyModel("iasp91")
    for dfidx, df in enumerate([df1, df2]):
        for staidx, sta in enumerate(df):
            for eqidx, time in enumerate(df[sta]):
                sta_coords = scs[dfidx][staidx][0].stats.coordinates
                event = catalog[eqidx]
                dist = locations2degrees(
                    sta_coords["latitude"],
                    sta_coords["longitude"],
                    event.latitude,
                    event.longitude,
                )
                if event.depth_km < 0:
                    depth = 0
                else:
                    depth = event.depth_km
                travel_time = model.get_travel_times(depth, dist, ["p", "P", "Pn"])[
                    0
                ].time
                abs_time = event.time + travel_time
                np.testing.assert_almost_equal(abs_time, time, decimal=1)


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_all_pickers()
    test_pphase_picker()
    test_p_pick()
    test_travel_time()
    test_get_travel_time_df()
    test_baer()
