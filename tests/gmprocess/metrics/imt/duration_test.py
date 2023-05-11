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
from gmprocess.metrics.reduction.duration import Duration
from gmprocess.utils.constants import TEST_DATA_DIR
from gmprocess.utils.event import ScalarEvent
from gmprocess.utils.config import get_config


def test_duration():
    data_file = TEST_DATA_DIR / "duration_data.json"
    with open(str(data_file), "rt", encoding="utf-8") as f:
        jdict = json.load(f)

    time = np.array(jdict["time"])
    # input output is m/s/s
    acc = np.array(jdict["acc"]) / 100
    target_d595 = jdict["d595"]
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
    # input is cm/s/s output is m/s/s
    trace = StationTrace(data=acc * 100, header=header)
    trace2 = trace.copy()
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
    config["metrics"]["output_imts"] = ["duration5-95"]
    config["metrics"]["output_imcs"] = ["ARITHMETIC_MEAN"]
    wmc = WaveformMetricCollection.from_streams([stream], event, config)
    wm = wmc.waveform_metrics[0].metric_list[0]

    np.testing.assert_allclose(
        wm.value("ARITHMETIC_MEAN"), target_d595, atol=1e-4, rtol=1e-4
    )


def test_duration575():
    datadir = TEST_DATA_DIR / "cosmos" / "us1000hyfh"
    data_file = str(datadir / "us1000hyfh_akbmrp_AKBMR--n.1000hyfh.BNZ.--.acc.V2c")
    stream = read_data(data_file)[0]

    dur = Duration(stream, interval=[5, 75])

    np.testing.assert_allclose(dur.result["HN1"], 45.325, atol=1e-4, rtol=1e-4)


if __name__ == "__main__":
    test_duration()
    test_duration575()


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_duration()
