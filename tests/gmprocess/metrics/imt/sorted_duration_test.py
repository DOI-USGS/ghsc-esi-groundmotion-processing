#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

import numpy as np

from gmprocess.io.read import read_data
from gmprocess.metrics.waveform_metric_collection import WaveformMetricCollection
from gmprocess.utils.constants import TEST_DATA_DIR
from gmprocess.utils.event import ScalarEvent
from gmprocess.utils.config import get_config


def test_sorted_duration():
    datadir = TEST_DATA_DIR / "cosmos" / "us1000hyfh"
    data_file = str(datadir / "us1000hyfh_akbmrp_AKBMR--n.1000hyfh.BNZ.--.acc.V2c")
    stream = read_data(data_file)[0]

    event = ScalarEvent.from_params(
        id="",
        lat=0,
        lon=0,
        depth=0,
        magnitude=0.0,
        mag_type="",
        time="2000-01-01 00:00:00",
    )

    config = get_config()
    config["metrics"]["output_imts"] = ["sorted_duration"]
    config["metrics"]["output_imcs"] = ["channels"]
    wmc = WaveformMetricCollection.from_streams([stream], event, config)
    wm = wmc.waveform_metrics[0].metric_list[0]

    assert wm.__repr__() == "SortedDuration: CHANNELS=36.805"


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_sorted_duration()
