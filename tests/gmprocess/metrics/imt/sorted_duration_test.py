#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

import numpy as np

from gmprocess.io.read import read_data
from gmprocess.metrics.station_summary import StationSummary
from gmprocess.utils.constants import TEST_DATA_DIR
from gmprocess.utils.event import ScalarEvent


def test_sorted_duration():
    datadir = TEST_DATA_DIR / "cosmos" / "us1000hyfh"
    data_file = str(datadir / "us1000hyfh_akbmrp_AKBMR--n.1000hyfh.BNZ.--.acc.V2c")
    stream = read_data(data_file)[0]

    event = ScalarEvent()
    event.fromParams(
        id="",
        lat=0,
        lon=0,
        depth=0,
        magnitude=0.0,
        mag_type="",
        time="2000-01-01 00:00:00",
    )

    station = StationSummary.from_stream(
        stream, ["channels"], ["sorted_duration"], event=event
    )
    pgms = station.pgms
    sorted_duration = pgms.loc["SORTED_DURATION", "CHANNELS"].Result

    np.testing.assert_allclose(sorted_duration, 36.805, atol=1e-4, rtol=1e-4)


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_sorted_duration()
