# third party imports
import numpy as np

# local imports
from gmprocess.io.geonet.core import read_geonet
from gmprocess.metrics.waveform_metric_collection import WaveformMetricCollection
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.utils.event import ScalarEvent
from gmprocess.utils.config import get_config


def test_pgv():
    datafiles, _ = read_data_dir("geonet", "us1000778i", "20161113_110259_WTMC_20.V2A")
    datafile_v2 = datafiles[0]
    stream_v2 = read_geonet(datafile_v2)[0]
    pgv_target = {}
    for trace in stream_v2:
        vtrace = trace.copy()
        vtrace.integrate()
        pgv_target[vtrace.stats["channel"]] = np.abs(vtrace.max())

    event = ScalarEvent.from_params(
        id="",
        lat=0,
        lon=0,
        depth=0,
        magnitude=0.0,
        mag_type="",
        time="2000-01-01 00:00:00",
    )

    config = get_config()
    config["metrics"]["output_imts"] = ["pgv"]
    config["metrics"]["output_imcs"] = ["channels"]
    wmc = WaveformMetricCollection.from_streams([stream_v2], event, config)
    wm = wmc.waveform_metrics[0].metric_list[0]

    np.testing.assert_almost_equal(wm.value("H2"), pgv_target["HN2"])
    np.testing.assert_almost_equal(wm.value("H1"), pgv_target["HN1"])
    np.testing.assert_almost_equal(wm.value("Z"), pgv_target["HNZ"])
