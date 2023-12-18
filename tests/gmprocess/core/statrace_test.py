import pickle
import pathlib
import numpy as np

from invutils import get_inventory
from obspy.core.utcdatetime import UTCDateTime

from gmprocess.utils import constants
from gmprocess.io.read import read_data
from gmprocess.core.stationtrace import StationTrace
from gmprocess.utils.test_utils import read_data_dir


def test_trace():
    data = np.random.rand(1000)
    header = {
        "sampling_rate": 1,
        "npts": len(data),
        "network": "US",
        "location": "11",
        "station": "ABCD",
        "channel": "HN1",
        "starttime": UTCDateTime(2010, 1, 1, 0, 0, 0),
    }
    inventory = get_inventory()
    invtrace = StationTrace(data=data, header=header, inventory=inventory)
    invtrace.set_provenance("detrend", {"detrending_method": "demean"})
    invtrace.set_parameter("failed", True)
    invtrace.set_parameter("corner_frequencies", [1, 2, 3])
    invtrace.set_parameter("metadata", {"name": "Fred"})

    assert invtrace.get_provenance("detrend")[0]["prov_attributes"] == {
        "detrending_method": "demean"
    }
    assert invtrace.get_parameter("failed")
    assert invtrace.get_parameter("corner_frequencies") == [1, 2, 3]
    assert invtrace.get_parameter("metadata") == {"name": "Fred"}

    prov = invtrace.provenance.get_prov_series()
    assert prov.iloc[0] == "demean"


def test_filters():
    data_files, _ = read_data_dir("geonet", "us1000778i", "20161113_110259_WTMC_20.V1A")
    streams = []
    for f in data_files:
        streams += read_data(f)

    # Shorten window for testing
    for tr in streams[0]:
        tr.data = tr.data[7000:10000]

    test_tr = StationTrace(
        data=tr.data,
        header={
            "channel": "HN1",
            "delta": tr.stats.delta,
            "npts": len(tr.data),
            "standard": {
                "corner_frequency": np.nan,
                "station_name": "",
                "source": "json",
                "instrument": "",
                "instrument_period": np.nan,
                "source_format": "json",
                "comments": "",
                "structure_type": "",
                "sensor_serial_number": "",
                "process_level": "raw counts",
                "process_time": "",
                "source_file": "",
                "horizontal_orientation": np.nan,
                "vertical_orientation": np.nan,
                "units": "cm/s/s",
                "units_type": "acc,",
                "instrument_sensitivity": np.nan,
                "volts_to_counts": np.nan,
                "instrument_damping": np.nan,
            },
        },
    )

    ddir = pathlib.Path(constants.TEST_DATA_DIR / "core")
    with open(ddir / "statest_filters.pkl", "rb") as f:
        target_dict = pickle.load(f)

    filter_dict = {}
    for filter_type in ["lowpass", "highpass", "bandpass", "bandstop"]:
        tr = test_tr.copy()
        fkey = filter_type + "_freq"
        filter_dict[fkey] = tr.filter(
            f"{filter_type}",
            freq=0.05,
            freqmin=0.05,
            freqmax=10.0,
            corners=4.0,
            zerophase=False,
            frequency_domain=True,
        ).data
        tr = test_tr.copy()
        fkey = filter_type + "_time"
        filter_dict[fkey] = test_tr.filter(
            f"{filter_type}",
            freq=0.05,
            freqmin=0.05,
            freqmax=10.0,
            corners=4.0,
            zerophase=False,
            frequency_domain=False,
        ).data

        np.testing.assert_allclose(
            filter_dict[filter_type + "_freq"],
            target_dict[filter_type + "_freq"],
            atol=1e-7,
        )
        np.testing.assert_allclose(
            filter_dict[filter_type + "_time"],
            target_dict[filter_type + "_time"],
            atol=1e-7,
        )
