import os

import numpy as np

from gmprocess.io.geonet.core import read_geonet
from gmprocess.utils.tests_utils import read_data_dir
from gmprocess.metrics.waveform_metric_collection import WaveformMetricCollection
from gmprocess.core.stationstream import StationStream
from gmprocess.core.stationtrace import StationTrace
from gmprocess.utils.config import get_config
from gmprocess.utils import constants
from gmprocess.core import scalar_event


def test_rotd():
    datadir = constants.TEST_DATA_DIR / "process"
    # Create a stream and station summary, convert from m/s^2 to cm/s^2 (GAL)
    osc1_data = np.genfromtxt(datadir / "ALCTENE.UW..sac.acc.final.txt")
    osc2_data = np.genfromtxt(datadir / "ALCTENN.UW..sac.acc.final.txt")
    osc1_data = osc1_data.T[1] * 100
    osc2_data = osc2_data.T[1] * 100
    tr1 = StationTrace(
        data=osc1_data,
        header={
            "channel": "HN1",
            "delta": 0.01,
            "npts": 24001,
            "coordinates": {
                "latitude": 44.5,
                "longitude": -122.3,
                "elevation": 0.0,
            },
            "standard": {
                "corner_frequency": np.nan,
                "station_name": "",
                "source": "json",
                "instrument": "",
                "instrument_period": np.nan,
                "source_format": "json",
                "comments": "",
                "source_file": "",
                "structure_type": "",
                "horizontal_orientation": np.nan,
                "vertical_orientation": np.nan,
                "sensor_serial_number": "",
                "process_level": "corrected physical units",
                "process_time": "",
                "units": "cm/s/s",
                "units_type": "acc",
                "instrument_sensitivity": np.nan,
                "volts_to_counts": np.nan,
                "instrument_damping": np.nan,
            },
        },
    )
    tr2 = StationTrace(
        data=osc2_data,
        header={
            "channel": "HN2",
            "delta": 0.01,
            "npts": 24001,
            "coordinates": {
                "latitude": 44.5,
                "longitude": -122.3,
                "elevation": 0.0,
            },
            "standard": {
                "corner_frequency": np.nan,
                "station_name": "",
                "source": "json",
                "instrument": "",
                "instrument_period": np.nan,
                "source_format": "json",
                "comments": "",
                "structure_type": "",
                "source_file": "",
                "horizontal_orientation": np.nan,
                "vertical_orientation": np.nan,
                "sensor_serial_number": "",
                "process_level": "corrected physical units",
                "process_time": "",
                "units": "cm/s/s",
                "units_type": "acc",
                "instrument_sensitivity": np.nan,
                "volts_to_counts": np.nan,
                "instrument_damping": np.nan,
            },
        },
    )
    st = StationStream([tr1, tr2])

    for tr in st:
        response = {"input_units": "counts", "output_units": "cm/s^2"}
        tr.set_provenance("remove_response", response)

    target_pga50 = 4.1221200279448444
    target_sa1050 = 10.716249471749395
    target_pgv50 = 6.2243050413999645
    target_sa0350 = 10.091461811808575
    target_sa3050 = 1.1232860465386469
    # Dummy event
    event = scalar_event.ScalarEvent.from_params(
        id="",
        latitude=44.0,
        longitude=-123.0,
        depth_km=0,
        magnitude=0.0,
        time="2000-01-01 00:00:00",
    )

    config = get_config()
    config["metrics"]["output_imts"] = ["pga", "pgv", "sa"]
    config["metrics"]["sa"]["periods"]["defined_periods"] = [0.3, 1.0, 3.0]
    config["metrics"]["output_imcs"] = ["rotd50"]
    wmc = WaveformMetricCollection.from_streams([st], event, config)
    wml = wmc.waveform_metrics[0].metric_list

    wml_values = [w.value("ROTD(50.0)") for w in wml]
    target_vlues = [
        4.1221200279448444,
        6.2243050413999645,
        10.091461811808575,
        10.716249471749395,
        1.1232860465386469,
    ]

    np.testing.assert_allclose(wml_values, target_vlues)


def test_exceptions():
    datafiles, event = read_data_dir(
        "geonet", "us1000778i", "20161113_110259_WTMC_20.V2A"
    )
    datafile_v2 = datafiles[0]
    stream_v2 = read_geonet(datafile_v2)[0]
    stream1 = stream_v2.select(channel="HN1")

    config = get_config()
    config["metrics"]["output_imts"] = ["pga"]
    config["metrics"]["output_imcs"] = ["rotd50"]
    wmc = WaveformMetricCollection.from_streams([stream1], event, config)
    wm = wmc.waveform_metrics[0].metric_list[0]
    assert np.isnan(wm.value("ROTD(50.0)"))
