#!/usr/bin/env python

import os

from gmprocess.io.bhrc.core import is_bhrc, read_bhrc
from gmprocess.utils.test_utils import read_data_dir


def test_bhrc():
    datafiles, _ = read_data_dir("bhrc", "usp000jq5p")

    # make sure format checker works
    assert is_bhrc(datafiles[0])

    raw_streams = []
    for dfile in datafiles:
        raw_streams += read_bhrc(dfile)


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_bhrc()
