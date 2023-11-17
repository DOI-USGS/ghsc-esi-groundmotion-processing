from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.metrics.waveform_metric_collection import WaveformMetricCollection
from gmprocess.utils import constants
from gmprocess.core.streamcollection import StreamCollection


def test_waveform_metric_collection():
    ddir = constants.TEST_DATA_DIR / "demo_steps" / "exports" / "ci38457511"
    ws_file = ddir / "workspace.h5"

    ws = StreamWorkspace(ws_file)
    wmc = WaveformMetricCollection.from_workspace(ws)
    assert wmc.__repr__() == "WaveformMetricCollection: 3 stations"

    stream_dir = constants.TEST_DATA_DIR / "dmg" / "ci15481673"
    streams = StreamCollection.from_directory(stream_dir)
    event = ws.get_event("ci38457511")
    config = ws.config
    config["metrics"]["sa"]["periods"]["defined_periods"] = [1.0]
    config["metrics"]["output_imts"] = ["SA"]
    wmc2 = WaveformMetricCollection.from_streams(streams, event, config)
    assert wmc2.__repr__() == "WaveformMetricCollection: 2 stations"
