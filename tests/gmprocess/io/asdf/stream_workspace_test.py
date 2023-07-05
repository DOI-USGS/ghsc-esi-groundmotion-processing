#!/usr/bin/env python

import os
import shutil
import tempfile
from pathlib import Path

import numpy as np
import pytest
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.utils import constants
from gmprocess.utils.config import get_config, update_config
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.waveform_processing.processing import process_streams

CONFIG = get_config()


def assert_cmp_with_nans(d1, d2):
    for key, v1 in d1.items():
        if key not in d2:
            raise AssertionError(f"{key} not in both compared dictionaries.")
        v2 = d2[key]
        if isinstance(v1, str):
            assert v1 == v2
        else:
            np.testing.assert_allclose(v1, v2, atol=1e-2)


def test_stream_workspace():
    CONFIG["metrics"]["output_imcs"] = ["channels"]
    eventid = "usb000syza"
    datafiles, event = read_data_dir("knet", eventid, "*")
    datadir = Path(datafiles[0]).parent
    raw_streams = StreamCollection.from_directory(datadir)
    config = update_config(datadir / "config_min_freq_0p2.yml", CONFIG)
    newconfig = config.copy()
    newconfig["processing"].append(
        {"nnet_qa": {"acceptance_threshold": 0.5, "model_name": "CantWell"}}
    )
    processed_streams = process_streams(raw_streams.copy(), event, config=newconfig)

    tdir = Path(tempfile.mkdtemp())
    try:
        tfile = tdir / "test.hdf"
        workspace = StreamWorkspace(tfile)
        workspace.add_event(event)
        workspace.add_streams(event, raw_streams, label="raw")
        workspace.add_streams(event, processed_streams, label="processed")
        assert workspace.__repr__() == "Events: 1 Stations: 2 Streams: 4"
        lab_df = workspace.summarize_labels()
        assert lab_df.shape == (2, 6)
        inv = workspace.get_inventory()
        assert inv.source == (
            "Japan National Research Institute for Earth Science and Disaster "
            "Resilience"
        )
        workspace.close()
    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tdir, ignore_errors=True)


def test_stream_workspace_ucla_review():
    reviewed_workspace = constants.TEST_DATA_DIR / "ucla_review" / "workspace.h5"
    ws = StreamWorkspace.open(reviewed_workspace)
    st = ws.get_streams("se60324281")
    assert len(st) == 8


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_stream_workspace()
    test_stream_workspace_ucla_review()
