# third party imports
import numpy as np

# local imports
from gmprocess.io.geonet.core import read_geonet
from gmprocess.metrics.waveform_metric_collection import WaveformMetricCollection
from gmprocess.utils import test_utils
from gmprocess.utils import event_utils
from gmprocess.utils.config import get_config


def test_sa():
    datafiles, _ = test_utils.read_data_dir(
        "geonet", "us1000778i", "20161113_110259_WTMC_20.V2A"
    )
    datafile_v2 = datafiles[0]
    stream_v2 = read_geonet(datafile_v2)[0]
    sa_target = {}
    for trace in stream_v2:
        vtrace = trace.copy()
        vtrace.integrate()
        sa_target[vtrace.stats["channel"]] = np.abs(vtrace.max())

    event = event_utils.ScalarEvent.from_params(
        id="",
        latitude=0,
        longitude=0,
        depth_km=0,
        magnitude=0.0,
        time="2000-01-01 00:00:00",
    )

    config = get_config()
    config["metrics"]["output_imts"] = ["sa"]
    config["metrics"]["sa"]["periods"]["defined_periods"] = [1.0]
    config["metrics"]["output_imcs"] = ["channels", "rotd50"]
    wmc = WaveformMetricCollection.from_streams([stream_v2], event, config)
    wm = wmc.waveform_metrics[0].metric_list[0]

    np.testing.assert_allclose(wm.value("H1"), 136.25041187387066)
    np.testing.assert_allclose(wm.value("H2"), 84.69296738413027)
    np.testing.assert_allclose(wm.value("ROTD(50.0)"), 106.03202302692148)
