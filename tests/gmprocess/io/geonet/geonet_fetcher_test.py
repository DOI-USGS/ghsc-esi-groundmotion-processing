#!/usr/bin/env python

import shutil
import tempfile
from pathlib import Path
from datetime import datetime

from gmprocess.io.geonet.geonet_fetcher import GeoNetFetcher
from gmprocess.utils.test_utils import vcr


def _test_GeoNetFetcher():
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        eqdict = {
            "id": "usp000hk1b",
            "time": datetime(2010, 9, 1, 21, 24, 45),
            "lat": -40.019,
            "lon": 172.999,
            "depth": 52.8,
            "mag": 4.2,
        }

        fetcher = GeoNetFetcher(
            eqdict["time"],
            eqdict["lat"],
            eqdict["lon"],
            eqdict["depth"],
            eqdict["mag"],
            rawdir=tmp_dir,
        )
        events = fetcher.getMatchingEvents(solve=False)
        assert len(events) == 1
        stream_collection = fetcher.retrieveData(events[0])
        assert len(stream_collection) == 4
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    _test_GeoNetFetcher()
