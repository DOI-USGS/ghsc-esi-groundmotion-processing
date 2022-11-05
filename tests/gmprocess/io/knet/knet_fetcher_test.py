#!/usr/bin/env python

import shutil
import tempfile
from pathlib import Path
from datetime import datetime

from gmprocess.io.knet.knet_fetcher import KNETFetcher
from gmprocess.utils.test_utils import vcr


@vcr.use_cassette()
def test_KNETFetcher():
    user = ""
    passwd = ""
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        # us10003xen
        utime = datetime(2015, 11, 11, 15, 33, 24)
        eqlat = 24.452
        eqlon = 122.697
        eqdepth = 97.0
        eqmag = 5.0
        fetcher = KNETFetcher(
            utime,
            eqlat,
            eqlon,
            eqdepth,
            eqmag,
            user=user,
            password=passwd,
            rawdir=tmp_dir,
        )
        events = fetcher.getMatchingEvents(solve=False)
        assert len(events) == 1
        assert events[0]["mag"] == 5.0
        stream_collection = fetcher.retrieveData(events[0])
        assert len(stream_collection) == 3
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_KNETFetcher()
