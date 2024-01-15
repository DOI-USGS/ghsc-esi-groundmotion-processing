# third party imports
import numpy as np

# local imports
from gmprocess.io.geonet.core import read_geonet
from gmprocess.metrics.waveform_metric_collection import WaveformMetricCollection
from gmprocess.utils.config import get_config
from gmprocess.utils import tests_utils
from gmprocess.core import scalar_event


def test_pga():
    datafiles, _ = tests_utils.read_data_dir(
        "geonet", "us1000778i", "20161113_110259_WTMC_20.V2A"
    )
    datafile_v2 = datafiles[0]
    stream_v2 = read_geonet(datafile_v2)[0]
    event = scalar_event.ScalarEvent.from_params(
        id="",
        latitude=0,
        longitude=0,
        depth_km=0,
        magnitude=0.0,
        time="2000-01-01 00:00:00",
    )

    config = get_config()
    config["metrics"]["output_imts"] = ["pga", "sa", "saincorrect"]
    config["metrics"]["sa"]["periods"]["defined_periods"] = [1.0]
    config["metrics"]["output_imcs"] = [
        "channels",
        "greater_of_two_horizontals",
        "gmrotd0",
        "gmrotd50",
        "gmrotd100",
        "rotd50",
        "geometric_mean",
        "arithmetic_mean",
    ]
    wmc = WaveformMetricCollection.from_streams([stream_v2], event, config)
    wm = wmc.waveform_metrics[0].metric_list[0]

    np.testing.assert_allclose(wm.value("ARITHMETIC_MEAN"), 90.242335558014219)
    np.testing.assert_allclose(wm.value("GEOMETRIC_MEAN"), 89.791654017670112)
    np.testing.assert_allclose(wm.value("H2"), 81.234672390673683)
    np.testing.assert_allclose(wm.value("H1"), 99.249998725354743)
    np.testing.assert_almost_equal(wm.value("Z"), 183.77223618666929)
    np.testing.assert_allclose(
        wm.value("GREATER_OF_TWO_HORIZONTALS"), 99.249998725354743
    )

    np.testing.assert_allclose(wm.value("GMROTD(0.0)"), 83.487703753812113)
    np.testing.assert_allclose(wm.value("GMROTD(50.0)"), 86.758642638162982)
    np.testing.assert_allclose(wm.value("GMROTD(100.0)"), 89.791654017670112)
    np.testing.assert_allclose(wm.value("ROTD(50.0)"), 91.401785419354567)
