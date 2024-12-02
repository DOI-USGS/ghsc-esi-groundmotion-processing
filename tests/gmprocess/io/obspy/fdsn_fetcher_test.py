import copy
import os
import pathlib
import shutil
import tempfile
from datetime import datetime

import pytest
from gmprocess.io.obspy.fdsn_fetcher import FDSNFetcher
from gmprocess.utils.config import get_config


@pytest.fixture(scope="session")
def vcr_config():
    # note: set "record_mode" to "once" to record, then set to "none" when prior to
    # committing the test. Can also be "rewrite".
    return {"record_mode": "once", "filter_headers": []}


@pytest.mark.vcr
def skip_test_fetcher(config):
    conf = copy.deepcopy(config)

    rawdir = tempfile.mkdtemp()
    try:
        conf["fetchers"]["FDSNFetcher"]["domain"]["circular"]["maxradius"] = 0.1
        # 2014-08-24 10:20:44
        utime = datetime(2014, 8, 24, 10, 20, 44)
        eqlat = 38.215
        eqlon = -122.312
        eqdepth = 11.1
        eqmag = 6.0
        fetcher = FDSNFetcher(
            utime,
            eqlat,
            eqlon,
            eqdepth,
            eqmag,
            rawdir=rawdir,
            config=conf,
            stream_collection=False,
        )
        fetcher.retrieve_data()
        filenames = next(os.walk(rawdir), (None, None, []))[2]
        assert len(filenames) == 12
    except Exception as e:
        raise (e)
    finally:
        if os.path.exists(rawdir):
            shutil.rmtree(rawdir, ignore_errors=True)


# this function should not run in a pipeline since it's purpose is to verify that
# we get a consistent number of waveforms from all configured FDSN providers, and
# wrapping this in vcr would defeat the purpose of the test.
# The test can be run simply: `python fdsn_fetcher_test.py`
def threads_fetcher():
    config = get_config()
    conf = copy.deepcopy(config)

    with tempfile.TemporaryDirectory() as trawdir:
        rawdir = pathlib.Path(trawdir)
        conf["fetchers"]["FDSNFetcher"]["domain"]["circular"]["maxradius"] = 0.1
        # 2014-08-24 10:20:44
        utime = datetime.fromisoformat("2024-05-01 20:49:00")
        eqlat = 33.811
        eqlon = -117.645
        eqdepth = 4.6
        eqmag = 4.1
        fetcher = FDSNFetcher(
            utime,
            eqlat,
            eqlon,
            eqdepth,
            eqmag,
            rawdir=rawdir,
            config=conf,
            stream_collection=False,
        )
        fetcher.retrieve_data()
        filenames = next(os.walk(rawdir), (None, None, []))[2]
        print(f"{len(filenames)} filenames found.")
        assert len(filenames) == 14


if __name__ == "__main__":
    threads_fetcher()
