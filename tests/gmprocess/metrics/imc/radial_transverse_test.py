import numpy as np
import scipy.constants as sp
from obspy import read, read_inventory
from obspy.geodetics import gps2dist_azimuth
from obspy.core.utcdatetime import UTCDateTime

from gmprocess.core.stationstream import StationStream
from gmprocess.core.stationtrace import StationTrace
from gmprocess.metrics.waveform_metric_collection import WaveformMetricCollection
from gmprocess.utils.config import get_config
from gmprocess.utils import constants
from gmprocess.core import scalar_event

datadir = constants.TEST_DATA_DIR / "fdsnfetch"


def test_radial_transverse():
    event = scalar_event.ScalarEvent.from_params(
        id="test",
        latitude=47.149,
        longitude=-122.7266667,
        depth_km=0,
        magnitude=5.0,
        time=UTCDateTime.strptime("2016-11-13 11:02:56", "%Y-%m-%d %H:%M:%S"),
    )
    st = read(str(datadir / "resp_cor" / "UW.ALCT.--.*.MSEED"))

    st[0].stats.standard = {}
    st[0].stats.standard["horizontal_orientation"] = 0.0
    st[0].stats["channel"] = "HN1"
    st[1].stats.standard = {}
    st[1].stats.standard["horizontal_orientation"] = 90.0
    st[1].stats["channel"] = "HN2"
    st[2].stats.standard = {}
    st[2].stats.standard["horizontal_orientation"] = np.nan
    st[2].stats["channel"] = "HNZ"

    inv = read_inventory(datadir / "inventory.xml")
    stalat, stalon = inv[0][0][0].latitude, inv[0][0][0].longitude

    for tr in st:
        tr.stats["coordinates"] = {"latitude": stalat}
        tr.stats["coordinates"]["longitude"] = stalon
        tr.stats["standard"].update(
            {
                "corner_frequency": np.nan,
                "station_name": "",
                "source": "json",
                "instrument": "",
                "instrument_period": np.nan,
                "vertical_orientation": np.nan,
                "source_format": "json",
                "comments": "",
                "structure_type": "",
                "source_file": "",
                "sensor_serial_number": "",
                "process_level": "raw counts",
                "process_time": "",
                "units": "cm/s/s",
                "units_type": "acc",
                "instrument_sensitivity": np.nan,
                "volts_to_counts": np.nan,
                "instrument_damping": np.nan,
            }
        )
    baz = gps2dist_azimuth(stalat, stalon, event.latitude, event.longitude)[1]

    st1 = st.copy()
    st1[0].stats.channel = st1[0].stats.channel[:-1] + "N"
    st1[1].stats.channel = st1[1].stats.channel[:-1] + "E"
    st1.rotate(method="NE->RT", back_azimuth=baz)
    pgms = np.abs(st1.max())

    st2 = StationStream([])
    for t in st:
        st2.append(StationTrace(t.data, t.stats))

    for tr in st2:
        response = {"input_units": "counts", "output_units": "cm/s^2"}
        tr.set_provenance("remove_response", response)

    config = get_config()
    config["metrics"]["output_imts"] = ["pga"]
    config["metrics"]["output_imcs"] = ["radial_transverse"]
    wmc = WaveformMetricCollection.from_streams([st2], event, config)
    wm = wmc.waveform_metrics[0].metric_list[0]

    R = wm.value("HNR")
    T = wm.value("HNT")

    np.testing.assert_almost_equal(pgms[0], sp.g * R)
    np.testing.assert_almost_equal(pgms[1], sp.g * T)

    # Test with a station whose channels are not aligned to E-N
    SEW_st = read(datadir / "resp_cor" / "GS.SEW.*.mseed")
    SEW_inv = read_inventory(datadir / "inventory_sew.xml")
    stalat, stalon = inv[0][0][0].latitude, inv[0][0][0].longitude

    # Test failure case without two horizontal channels
    copy1 = st2.copy()
    copy1[0].stats.channel = copy1[0].stats.channel[:-1] + "3"

    wmc = WaveformMetricCollection.from_streams([copy1], event, config)
    wm = wmc.waveform_metrics[0].metric_list[0]
    assert np.isnan(wm.value("HNR"))
    assert np.isnan(wm.value("HNT"))

    # Test failure case when channels are not orthogonal
    copy3 = st2.copy()
    copy3[0].stats.standard.horizontal_orientation = 100
    wmc = WaveformMetricCollection.from_streams([copy3], event, config)
    wm = wmc.waveform_metrics[0].metric_list[0]

    assert np.isnan(wm.value("HNR"))
    assert np.isnan(wm.value("HNT"))
