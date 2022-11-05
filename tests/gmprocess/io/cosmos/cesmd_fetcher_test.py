#!/usr/bin/env python

import shutil
import tempfile
from pathlib import Path
from datetime import datetime

from gmprocess.io.cosmos.cesmd_fetcher import CESMDFetcher
from gmprocess.utils.test_utils import vcr


@vcr.use_cassette()
def test_CESMDFetcher():
    # note that since the email is passed in via the url, after running this with a
    # legit email, we have to go into the cassette and modify the email in the url
    # to mach "testemail" so that the casette matches.
    email = "testemail"
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        # nc73792396
        utime = datetime(2022, 10, 12, 0, 28, 36)
        eqlat = 38.5498
        eqlon = -119.4412
        eqdepth = 7.3
        eqmag = 3.5
        fetcher = CESMDFetcher(
            utime, eqlat, eqlon, eqdepth, eqmag, email=email, rawdir=tmp_dir
        )
        events = fetcher.getMatchingEvents(solve=False)
        assert len(events) == 1
        assert events[0]["mag"] == eqmag
        stream_collection = fetcher.retrieveData(events[0])
        assert len(stream_collection) == 1
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_CESMDFetcher()
