#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

# third party imports
import numpy as np

# local imports
from gmprocess.io.geonet.core import read_geonet
from gmprocess.metrics.waveform_metric_collection import WaveformMetricCollection
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.utils.config import get_config


def test_gmrotd():
    datafiles, event = read_data_dir(
        "geonet", "us1000778i", "20161113_110259_WTMC_20.V2A"
    )
    datafile_v2 = datafiles[0]
    config = get_config()
    config["metrics"]["output_imts"] = ["pga"]
    config["metrics"]["output_imcs"] = ["gmrotd50"]
    stream_v2 = read_geonet(datafile_v2)[0]
    wmc = WaveformMetricCollection.from_streams([stream_v2], event, config)
    wm = wmc.waveform_metrics[0].metric_list[0]
    np.testing.assert_almost_equal(wm.value("GMROTD(50.0)"), 86.75864263816298)


def test_exceptions():
    datafiles, event = read_data_dir(
        "geonet", "us1000778i", "20161113_110259_WTMC_20.V2A"
    )
    datafile_v2 = datafiles[0]
    stream_v2 = read_geonet(datafile_v2)[0]
    stream1 = stream_v2.select(channel="HN1")
    config = get_config()
    config["metrics"]["output_imts"] = ["pga"]
    config["metrics"]["output_imcs"] = ["gmrotd50"]
    wmc = WaveformMetricCollection.from_streams([stream1], event, config)
    wm = wmc.waveform_metrics[0].metric_list[0]
    assert np.isnan(wm.value("GMROTD(50.0)"))

    for trace in stream_v2:
        stream1.append(trace)
    wmc = WaveformMetricCollection.from_streams([stream1], event, config)
    assert np.isnan(wm.value("GMROTD(50.0)"))


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_gmrotd()
    test_exceptions()
