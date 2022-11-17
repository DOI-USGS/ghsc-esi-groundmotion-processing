#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

import numpy as np
import csv

from obspy.core.trace import Stats

from gmprocess.core.stationstream import StationStream
from gmprocess.core.stationtrace import StationTrace
from gmprocess.metrics.station_summary import StationSummary
from gmprocess.utils.constants import TEST_DATA_DIR
from gmprocess.utils.event import ScalarEvent


def read_at2(dfile, horient=0.0):
    # This is a conveneince method so we can read in these specific data for
    # testing, it is not a general purpose reader since this format does not
    # contain a lot of metadata that is generally required for it to be useful.
    skiprows = 4
    datafile = open(dfile, "r", encoding="utf-8")
    datareader = csv.reader(datafile)
    data = []
    header = []
    # for i in range(skiprows):
    # next(datareader)
    #    header.append(datareader.readlines())
    count = 0
    for row in datareader:
        if count < skiprows:
            header.append(row)
        else:
            data.extend([float(e) for e in row[0].split()])
        count += 1
    datafile.close()

    hdr = {}
    hdr["network"] = ""
    hdr["station"] = ""
    if horient == 0:
        hdr["channel"] = "BH1"
    else:
        hdr["channel"] = "BH2"
    hdr["location"] = "--"

    dt = float(header[3][1].split("=")[1].strip().lower().replace("sec", ""))
    hdr["npts"] = len(data)
    hdr["sampling_rate"] = 1 / dt
    hdr["duration"] = (hdr["npts"] - 1) / hdr["sampling_rate"]

    hdr["starttime"] = 0

    # There is no lat/lon...
    hdr["coordinates"] = {"latitude": 0.0, "longitude": 0.0, "elevation": 0.0}

    standard = {}
    standard["units_type"] = "acc"
    standard["units"] = "cm/s^2"  # actually g but we convert later
    standard["horizontal_orientation"] = horient
    standard["vertical_orientation"] = np.nan
    standard["source_file"] = dfile
    standard["station_name"] = ""
    standard["corner_frequency"] = 30.0
    standard["structure_type"] = ""
    standard["comments"] = ""
    standard["instrument"] = ""
    standard["instrument_period"] = 1.0
    standard["instrument_sensitivity"] = 1.0
    standard["source"] = "PEER"
    standard["instrument_damping"] = 0.1
    standard["sensor_serial_number"] = ""
    standard["process_level"] = "corrected physical units"
    standard["source_format"] = "AT2"
    standard["process_time"] = ""
    standard["volts_to_counts"] = np.nan
    hdr["standard"] = standard
    # convert data from g to cm/s^2
    g_to_cmss = 980.665
    tr = StationTrace(np.array(data.copy()) * g_to_cmss, Stats(hdr.copy()))
    response = {"input_units": "counts", "output_units": "cm/s^2"}
    tr.setProvenance("remove_response", response)
    return tr


def test_high_freq_sa():
    # Dummy event
    event = ScalarEvent()
    event.fromParams(
        id="", time="20001-01 00:00:00", lat=0, lon=0, depth=0, magnitude=0
    )
    t1 = time.time()
    datadir = TEST_DATA_DIR / "high_freq_sa"
    fnames = [
        "RSN10590_ComalTX11-10-20_IU.CCM.BH1.00.AT2",
        "RSN10590_ComalTX11-10-20_IU.CCM.BH2.00.AT2",
    ]
    dfile = datadir / fnames[0]
    h1 = read_at2(str(dfile))
    dfile = datadir / fnames[1]
    h2 = read_at2(str(dfile), horient=90.0)
    st = StationStream([h1, h2])

    # shorten window to speed up tests
    for tr in st:
        tr.data = tr.data[5320:9260]

    periods = [0.01, 0.02, 0.03, 0.05, 0.075, 0.1, 0.15, 0.2]
    imt_list = [f"sa{p}" for p in periods]
    station = StationSummary.from_stream(st, ["rotd50"], imt_list, event=event)
    # I believe that units are %g in the following table:
    pgmdf = station.pgms
    imt_strs = [f"SA({p:.3f})" for p in periods]
    test_sa = []
    for i in imt_strs:
        test_sa.append(pgmdf.loc[i, "ROTD(50.0)"].Result)

    # Target (from PEER NGA East Flatfile)
    test_data = {
        "periods": periods,
        "target_sa": [
            0.00000265693,
            0.00000265828,
            0.00000263894,
            0.00000265161,
            0.00000260955,
            0.0000026616,
            0.00000276549,
            0.00000308482,
        ],
        "test_sa": np.array(test_sa) / 100,
    }

    np.testing.assert_allclose(test_data["target_sa"], test_data["test_sa"], rtol=0.1)
    t2 = time.time()
    elapsed = t2 - t1
    print(f"Test duration: {elapsed}")


if __name__ == "__main__":
    test_high_freq_sa()
