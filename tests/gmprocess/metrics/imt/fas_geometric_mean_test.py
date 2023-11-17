import re

import numpy as np
import pandas as pd

from gmprocess.metrics.waveform_metric_collection import WaveformMetricCollection
from gmprocess.core.stationstream import StationStream
from gmprocess.core.stationtrace import StationTrace
from gmprocess.utils.constants import TEST_DATA_DIR
from gmprocess.utils.config import get_config
from gmprocess.utils.event import ScalarEvent


def test_fas():
    """
    Testing based upon the work provided in
    https://github.com/arkottke/notebooks/blob/master/effective_amp_spectrum.ipynb
    """
    fas_file = TEST_DATA_DIR / "fas_geometric_mean.pkl"
    p1 = str(TEST_DATA_DIR / "peer" / "RSN763_LOMAP_GIL067.AT2")
    p2 = str(TEST_DATA_DIR / "peer" / "RSN763_LOMAP_GIL337.AT2")

    stream = StationStream([])
    for idx, fpath in enumerate([p1, p2]):
        with open(fpath, encoding="utf-8") as file_obj:
            for _ in range(3):
                next(file_obj)
            meta = re.findall(r"[.0-9]+", next(file_obj))
            dt = float(meta[1])
            accels = np.array(
                [col for line in file_obj for col in line.split()], dtype=float
            )
        trace = StationTrace(
            data=accels,
            header={
                "channel": "HN" + str(idx),
                "delta": dt,
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
                    "source_file": "",
                    "process_level": "raw counts",
                    "process_time": "",
                    "horizontal_orientation": np.nan,
                    "vertical_orientation": np.nan,
                    "units": "cm/s/s",
                    "units_type": "acc",
                    "instrument_sensitivity": np.nan,
                    "volts_to_counts": np.nan,
                    "instrument_damping": np.nan,
                },
            },
        )
        stream.append(trace)

    for tr in stream:
        response = {"input_units": "counts", "output_units": "cm/s^2"}
        tr.set_provenance("remove_response", response)

    target_df = pd.read_pickle(fas_file)
    ind_vals = target_df.index.values
    per = np.unique([float(i[0].split(")")[0].split("(")[1]) for i in ind_vals])
    per = per[[20, 85, 160]]
    freqs = 1 / per
    imts = ["fas" + str(p) for p in per]
    config = get_config()
    event = ScalarEvent.from_params(
        id="",
        lat=37.0,
        lon=-122.0,
        depth=0,
        magnitude=0.0,
        mag_type="",
        time="2000-01-01 00:00:00",
    )

    config["metrics"]["output_imts"] = ["fas"]
    config["metrics"]["output_imcs"] = ["geometric_mean"]
    config["metrics"]["fas"]["periods"]["use_array"] = False
    config["metrics"]["fas"]["periods"]["defined_periods"] = per.tolist()
    wmc = WaveformMetricCollection.from_streams([stream], event, config)
    wml = wmc.waveform_metrics[0]
    target_repr = (
        "3 metric(s) in list:\n  FAS(T=0.0300, B=20.0): GEOMETRIC_MEAN=0.001\n"
        "  FAS(T=0.1410, B=20.0): GEOMETRIC_MEAN=0.030\n"
        "  FAS(T=0.7940, B=20.0): GEOMETRIC_MEAN=0.028\n"
    )
    assert wml.__repr__() == target_repr
