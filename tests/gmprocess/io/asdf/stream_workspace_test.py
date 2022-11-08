#!/usr/bin/env python

import os
import shutil
import tempfile
import pytest
from pathlib import Path

import pandas as pd

from gmprocess.core.streamcollection import StreamCollection
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.metrics.station_summary import StationSummary
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.utils.config import update_config, get_config
from gmprocess.utils import constants
from gmprocess.waveform_processing.processing import process_streams

import numpy as np

CONFIG = get_config()


def test_stream_workspace_methods():
    tdir = Path(tempfile.mkdtemp())
    try:
        eventid = "usb000syza"
        datafiles, event = read_data_dir("knet", eventid, "*")
        datadir = Path(datafiles[0]).parent
        raw_streams = StreamCollection.from_directory(datadir)

        ws = StreamWorkspace.create(tdir / "workspace.h5")
        with pytest.raises(KeyError):
            ws.calcMetrics(eventid)

        ws.addEvent(event)
        tabs = ws.getTables(label="raw", config=CONFIG)
        assert isinstance(tabs[0], pd.core.frame.DataFrame)
        assert tabs[1] == {}
        assert tabs[2] == {}

        ws.addStreams(event, raw_streams, label="raw", overwrite=True)

        sm = ws.getStreamMetrics(eventid, "CI", "XX", "raw")
        assert sm is None

        ws.close()
        with pytest.raises(OSError):
            StreamWorkspace.open(tdir / "nonexistance_file.h5")

    except BaseException as e:
        raise e
    finally:
        shutil.rmtree(tdir, ignore_errors=True)


def test_stream_workspace():
    CONFIG["metrics"]["output_imcs"] = ["channels"]
    eventid = "usb000syza"
    datafiles, event = read_data_dir("knet", eventid, "*")
    datadir = Path(datafiles[0]).parent
    raw_streams = StreamCollection.from_directory(datadir)
    config = update_config(datadir / "config_min_freq_0p2.yml", CONFIG)
    newconfig = config.copy()
    newconfig["processing"].append(
        {"NNet_QA": {"acceptance_threshold": 0.5, "model_name": "CantWell"}}
    )
    processed_streams = process_streams(raw_streams.copy(), event, config=newconfig)

    tdir = Path(tempfile.mkdtemp())
    try:
        tfile = tdir / "test.hdf"
        workspace = StreamWorkspace(tfile)
        workspace.addEvent(event)
        workspace.addStreams(event, raw_streams, label="raw")
        workspace.addStreams(event, processed_streams, label="processed")
        assert workspace.__repr__() == "Events: 1 Stations: 2 Streams: 4"
        lab_df = workspace.summarizeLabels()
        assert lab_df.shape == (2, 6)
        inv = workspace.getInventory()
        assert inv.source == (
            "Japan National Research Institute for Earth Science and Disaster "
            "Resilience"
        )

        stream1 = raw_streams[0]
        # Get metrics from station summary for raw streams
        config["metrics"]["sa"]["periods"]["defined_periods"] = [0.3, 1.0, 3.0]
        summary1 = StationSummary.from_config(stream1, config=config)
        s1_df_in = summary1.pgms.sort_values(["IMT", "IMC"])
        array1 = s1_df_in["Result"].to_numpy()

        # Compare to metrics from getStreamMetrics for raw streams
        workspace.calcMetrics(eventid, labels=["raw"], config=config)
        summary1_a = workspace.getStreamMetrics(
            event.id,
            stream1[0].stats.network,
            stream1[0].stats.station,
            "raw",
            config=config,
        )
        s1_df_out = summary1_a.pgms.sort_values(["IMT", "IMC"])
        array2 = s1_df_out["Result"].to_numpy()

        np.testing.assert_allclose(array1, array2, atol=1e-6, rtol=1e-6)
        workspace.close()
    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tdir, ignore_errors=True)


def test_stream_workspace_ucla_review():
    reviewed_workspace = constants.TEST_DATA_DIR / "ucla_review" / "workspace.h5"
    ws = StreamWorkspace.open(reviewed_workspace)
    st = ws.getStreams("se60324281")
    assert len(st) == 8


def test_getStreamMetrics():
    workspace = constants.TEST_DATA_DIR / "ucla_review" / "workspace.h5"
    ws = StreamWorkspace.open(workspace)
    # to raise warning that no metrics are available
    ws.getStreamMetrics("se60324281", "ET", "GFM", "default")

    workspace = (
        constants.TEST_DATA_DIR
        / "demo_steps"
        / "exports"
        / "ci38457511"
        / "workspace.h5"
    )
    ws = StreamWorkspace.open(workspace)
    sm = ws.getStreamMetrics("ci38457511", "CI", "CCC", "default")
    assert sm.pgms.shape == (104, 1)

    # Raises a warning that no stream was found
    ws.getStreamMetrics("ci38457511", "CI", "AAA", "default")


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_stream_workspace()
    test_stream_workspace_ucla_review()
    test_getStreamMetrics()
    test_stream_workspace_methods()
