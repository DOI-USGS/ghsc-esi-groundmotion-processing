# third party imports
from obspy.core.utcdatetime import UTCDateTime

# local imports
from gmprocess.io.geonet.core import read_geonet
from gmprocess.metrics.reduction.max import Max
from gmprocess.metrics.waveform_metric_collection import WaveformMetricCollection
from gmprocess.utils.config import get_config
from gmprocess.utils import event_utils
from gmprocess.utils import test_utils


def test_get_peak_time():
    datafiles, _ = test_utils.read_data_dir(
        "geonet", "us1000778i", "20161113_110259_WTMC_20.V2A"
    )
    datafile = datafiles[0]
    stream1 = read_geonet(datafile)[0]
    max_cls = Max(stream1).result
    assert len(max_cls) == 2

    max_cls = Max({"chan": [0, 1, 2, 3]}).result
    assert len(max_cls) == 1

    stream2 = read_geonet(datafile)[0]
    event = event_utils.ScalarEvent.from_params(
        id="us1000778i",
        latitude=-42.6925,
        longitude=173.021944,
        depth_km=0,
        magnitude=5.0,
        magnitude_type="",
        time="2016-11-13 11:02:56",
    )
    config = get_config()
    config["metrics"]["output_imts"] = ["PGA", "PGV"]
    config["metrics"]["output_imcs"] = ["channels"]
    WaveformMetricCollection.from_streams([stream2], event, config)
    assert stream2[0].stats.pga_time == UTCDateTime("2016-11-13T11:03:08.880001Z")
    assert stream2[0].stats.pgv_time == UTCDateTime("2016-11-13T11:03:10.580001Z")

    assert stream2[1].stats.pga_time == UTCDateTime("2016-11-13T11:03:09.960001Z")
    assert stream2[1].stats.pgv_time == UTCDateTime("2016-11-13T11:03:08.860001Z")

    assert stream2[2].stats.pga_time == UTCDateTime("2016-11-13T11:03:08.140001Z")
    assert stream2[2].stats.pgv_time == UTCDateTime("2016-11-13T11:03:09.560001Z")
