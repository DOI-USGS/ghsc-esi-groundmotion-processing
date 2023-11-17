from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.metrics.station_metric_collection import StationMetricCollection
from gmprocess.utils import constants
from gmprocess.utils.config import get_config
from gmprocess.core.streamcollection import StreamCollection


def test_station_metric_collection():
    config = get_config()
    ddir = constants.TEST_DATA_DIR / "demo_steps" / "exports" / "ci38457511"
    ws_file = ddir / "workspace.h5"

    ws = StreamWorkspace(ws_file)
    smc = StationMetricCollection.from_workspace(ws)
    assert smc.__repr__() == "StationMetricCollection: 3 metrics"

    stream_dir = constants.TEST_DATA_DIR / "dmg" / "ci15481673"
    streams = StreamCollection.from_directory(stream_dir)
    event = ws.get_event("ci38457511")
    smc2 = StationMetricCollection.from_streams(streams, event, config)
    assert smc2.__repr__() == "StationMetricCollection: 2 metrics"
