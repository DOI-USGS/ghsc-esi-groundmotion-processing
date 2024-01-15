# third party imports
import numpy as np

# local imports
from gmprocess.io.geonet.core import read_geonet
from gmprocess.metrics.waveform_metric_collection import WaveformMetricCollection
from gmprocess.utils.tests_utils import read_data_dir
from gmprocess.utils.config import get_config


def test_greater_of_two_horizontals():
    datafiles, event = read_data_dir(
        "geonet", "us1000778i", "20161113_110259_WTMC_20.V2A"
    )
    datafile_v2 = datafiles[0]
    stream_v2 = read_geonet(datafile_v2)[0]
    config = get_config()
    config["metrics"]["output_imts"] = ["pga"]
    config["metrics"]["output_imcs"] = ["greater_of_two_horizontals"]
    wmc = WaveformMetricCollection.from_streams([stream_v2], event, config)
    wm = wmc.waveform_metrics[0].metric_list[0]
    np.testing.assert_almost_equal(
        wm.value("GREATER_OF_TWO_HORIZONTALS"), 99.24999872535474
    )
