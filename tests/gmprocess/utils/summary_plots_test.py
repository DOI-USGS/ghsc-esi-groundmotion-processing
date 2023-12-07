# stdlib imports
import tempfile
import shutil

from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.utils import constants
from gmprocess.utils.summary_plots import SummaryPlot


def test_summary_plots():
    ddir = constants.TEST_DATA_DIR / "demo_steps" / "exports" / "ci38457511"
    ws = StreamWorkspace.open(ddir / "workspace.h5")
    event = ws.get_event("ci38457511")
    st = ws.get_streams("ci38457511", labels=["default"])[0]
    st_raw = ws.get_streams("ci38457511", labels=["unprocessed"])[0]
    tdir = tempfile.mkdtemp()
    try:
        sp = SummaryPlot(st, st_raw, tdir, event)
        sp.plot()
    except Exception as e:
        raise e
    finally:
        shutil.rmtree(tdir, ignore_errors=True)
