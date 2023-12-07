from gmprocess.io.read import read_data
from gmprocess.metrics.waveform_metric_collection import WaveformMetricCollection
from gmprocess.utils.config import get_config
from gmprocess.utils import constants
from gmprocess.utils import event_utils


def test_sorted_duration():
    datadir = constants.TEST_DATA_DIR / "cosmos" / "us1000hyfh"
    data_file = str(datadir / "us1000hyfh_akbmrp_AKBMR--n.1000hyfh.BNZ.--.acc.V2c")
    stream = read_data(data_file)[0]

    event = event_utils.ScalarEvent.from_params(
        id="",
        latitude=0,
        longitude=0,
        depth_km=0,
        magnitude=0.0,
        time="2000-01-01 00:00:00",
    )

    config = get_config()
    config["metrics"]["output_imts"] = ["sorted_duration"]
    config["metrics"]["output_imcs"] = ["channels"]
    wmc = WaveformMetricCollection.from_streams([stream], event, config)
    wm = wmc.waveform_metrics[0].metric_list[0]

    assert wm.__repr__() == "SortedDuration: CHANNELS=36.805"
