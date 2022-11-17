import os

# third party imports
from obspy.core.utcdatetime import UTCDateTime

# local imports
from gmprocess.io.geonet.core import read_geonet
from gmprocess.metrics.reduction.max import Max
from gmprocess.metrics.station_summary import StationSummary
from gmprocess.utils.event import ScalarEvent
from gmprocess.utils.test_utils import read_data_dir


def test_get_peak_time():
    datafiles, _ = read_data_dir("geonet", "us1000778i", "20161113_110259_WTMC_20.V2A")
    datafile = datafiles[0]
    stream1 = read_geonet(datafile)[0]
    max_cls = Max(stream1).result
    assert len(max_cls) == 2

    max_cls = Max({"chan": [0, 1, 2, 3]}).result
    assert len(max_cls) == 1

    stream2 = read_geonet(datafile)[0]
    event = ScalarEvent()
    event.fromParams(
        id="us1000778i",
        lat=-42.6925,
        lon=173.021944,
        depth=0,
        magnitude=5.0,
        mag_type="",
        time="2016-11-13 11:02:56",
    )
    stream_summary = StationSummary.from_stream(
        stream2, ["channels"], ["pgv", "pga"], event
    )
    assert stream2[0].stats.pga_time == UTCDateTime("2016-11-13T11:03:08.880001Z")
    assert stream2[0].stats.pgv_time == UTCDateTime("2016-11-13T11:03:10.580001Z")

    assert stream2[1].stats.pga_time == UTCDateTime("2016-11-13T11:03:09.960001Z")
    assert stream2[1].stats.pgv_time == UTCDateTime("2016-11-13T11:03:08.860001Z")

    assert stream2[2].stats.pga_time == UTCDateTime("2016-11-13T11:03:08.140001Z")
    assert stream2[2].stats.pgv_time == UTCDateTime("2016-11-13T11:03:09.560001Z")


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_get_peak_time()
