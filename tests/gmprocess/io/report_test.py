#!/usr/bin/env python

import shutil
import tempfile
from pathlib import Path

from gmprocess.io import report
from gmprocess.utils import constants
from gmprocess.io.asdf.stream_workspace import StreamWorkspace


def test_report():
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        eventdir = constants.TEST_DATA_DIR / "demo_steps" / "exports" / "ci38457511"
        ws_file = eventdir / "workspace.h5"
        ws = StreamWorkspace.open(ws_file)
        sc = ws.getStreams("ci38457511")
        origin = ws.getEvent("ci38457511")

        report.build_report_latex(
            st_list=sc.streams,
            directory=tmp_dir,
            origin=origin,
            prefix="pytest",
            build_latex=False,
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_report()
