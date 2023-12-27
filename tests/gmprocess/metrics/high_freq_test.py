import csv

import numpy as np

from obspy.core.trace import Stats

from gmprocess.core.stationstream import StationStream
from gmprocess.core.stationtrace import StationTrace
from gmprocess.metrics.waveform_metric_collection import WaveformMetricCollection
from gmprocess.utils import constants
from gmprocess.core import scalar_event
from gmprocess.utils.config import get_config


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
    tr.set_provenance("remove_response", response)
    return tr


def test_high_freq_sa():
    # Dummy event
    event = scalar_event.ScalarEvent.from_params(
        id="",
        time="20001-01 00:00:00",
        latitude=0,
        longitude=0,
        depth_km=0,
        magnitude=0,
    )
    datadir = constants.TEST_DATA_DIR / "high_freq_sa"
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

    periods = [0.01, 0.02, 0.03, 0.05, 0.075]

    config = get_config()
    config["metrics"]["output_imts"] = ["SA"]
    config["metrics"]["output_imcs"] = ["ROTD50"]
    config["metrics"]["sa"]["periods"]["defined_periods"] = periods
    wmc = WaveformMetricCollection.from_streams([st], event, config)
    metric_list = wmc.waveform_metrics[0]
    # convert to g from %g
    test_sa = [m.value("ROTD(50.0)") / 100 for m in metric_list.metric_list]

    # Target (from PEER NGA East Flatfile)
    target_sa = [
        0.00000265693,
        0.00000265828,
        0.00000263894,
        0.00000265161,
        0.00000260955,
    ]

    np.testing.assert_allclose(target_sa, test_sa, rtol=0.1)
