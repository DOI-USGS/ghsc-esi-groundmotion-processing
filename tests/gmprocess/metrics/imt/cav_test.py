#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json

import numpy as np

from gmprocess.io.read import read_data
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.metrics.waveform_metric_collection import WaveformMetricCollection
from gmprocess.core.stationstream import StationStream
from gmprocess.core.stationtrace import StationTrace
from gmprocess.utils.constants import TEST_DATA_DIR
from gmprocess.utils.event import ScalarEvent
from gmprocess.utils.config import get_config


def test_cav():
    data_file = TEST_DATA_DIR / "cav_data.json"
    with open(str(data_file), "rt", encoding="utf-8") as f:
        jdict = json.load(f)

    time = np.array(jdict["time"])
    # input output is m/s/s
    acc = np.array(jdict["acc"]) / 100
    target_CAV = jdict["cav"]
    delta = time[2] - time[1]
    sr = 1 / delta
    header = {
        "delta": delta,
        "sampling_rate": sr,
        "npts": len(acc),
        "channel": "HN1",
        "standard": {
            "corner_frequency": np.nan,
            "station_name": "",
            "source": "json",
            "source_file": "",
            "instrument": "",
            "instrument_period": np.nan,
            "source_format": "json",
            "comments": "",
            "structure_type": "",
            "sensor_serial_number": "",
            "process_level": "raw counts",
            "process_time": "",
            "horizontal_orientation": np.nan,
            "vertical_orientation": np.nan,
            "units": "m/s/s",
            "units_type": "acc",
            "instrument_sensitivity": np.nan,
            "volts_to_counts": np.nan,
            "instrument_damping": np.nan,
        },
    }
    # input is cm/s/s output is m/s/s #incorrectly stated?
    # input is m/s/s output is cm/s/s?
    trace = StationTrace(data=acc * 100, header=header)
    trace2 = trace.copy()
    trace2.data*=2
    trace2.stats.channel = "HN2"
    stream = StationStream([trace, trace2])

    for tr in stream:
        response = {"input_units": "counts", "output_units": "cm/s^2"}
        tr.set_provenance("remove_response", response)

    event = ScalarEvent.from_params(
        id="",
        lat=24.0,
        lon=120.0,
        depth=0,
        magnitude=0.0,
        mag_type="",
        time="2000-01-01 00:00:00",
    )

    config = get_config()
    config["metrics"]["output_imts"] = ["cav"]
    #config["metrics"]["output_imts"] = ["SA"]
    #config["metrics"]["output_imcs"] = ["ARITHMETIC_MEAN"]
    config["metrics"]["output_imcs"] = ["ARITHMETIC_MEAN","GEOMETRIC_MEAN"]
    #config["metrics"]["output_imcs"] = ["ROTD50.0"]
    #config["metrics"]["output_imcs"] = ["rotd50"]
    #CAV_gm = 874.7610785391253
    #CAV_am = 927.8242358296103

    #add the following to the Json file to have gm and am after computations, then two asserts
    target_CAV_am = jdict["cav"]["am"]
    target_CAV_gm = jdict["cav"]["gm"]

    wmc = WaveformMetricCollection.from_streams([stream], event, config)
    wm = wmc.waveform_metrics[0].metric_list[0]
    CAV = wm.value("ARITHMETIC_MEAN") * 100
    CAV_gm = wm.value("GEOMETRIC_MEAN") * 100

    #np.testing.assert_almost_equal(CAV, target_CAV, decimal=1)
    np.testing.assert_almost_equal(CAV, target_CAV_am, decimal=1)
    np.testing.assert_almost_equal(CAV_gm, target_CAV_gm, decimal=1)


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_cav()
