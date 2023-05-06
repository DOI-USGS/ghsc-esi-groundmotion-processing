#!/usr/bin/env python
# -*- coding: utf-8 -*-

# stdlib imports
import os.path
import tempfile
import shutil

from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.utils import constants
from gmprocess.utils.summary_plots import SummaryPlot


def test_summary_plots():
    ddir = constants.TEST_DATA_DIR / "demo_steps" / "exports" / "ci38457511"
    ws = StreamWorkspace.open(ddir / "workspace.h5")
    event = ws.getEvent("ci38457511")
    st = ws.getStreams(eventid="ci38457511")[0]
    tdir = tempfile.mkdtemp()
    try:
        sp = SummaryPlot(st, tdir, event)
        sp.plot()
    except Exception as e:
        raise e
    finally:
        shutil.rmtree(tdir, ignore_errors=True)


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_summary_plots()
