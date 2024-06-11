import numpy as np

from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.metrics.waveform_metric_collection import (
    WaveformMetricCollection,
)
from gmprocess.utils import constants


def test_waveform_metric_collection():
    ddir = constants.TEST_DATA_DIR / "demo_steps" / "exports" / "ci38457511"
    ws_file = ddir / "workspace.h5"

    ws = StreamWorkspace(ws_file)
    wmc = WaveformMetricCollection.from_workspace(ws)
    assert wmc.__repr__() == "WaveformMetricCollection: 3 stations"
    assert len(wmc.waveform_metrics) == 3
    for st_meta, st_metrics in zip(wmc.stream_metadata, wmc.waveform_metrics):
        if st_meta[0]["station"] != "CCC":
            continue
        wml = st_metrics.metric_list
        assert len(wml) == 26
        for metric in wml:
            if metric.type != "SA":
                continue
            if metric.metric_attributes["period"] != 1.0:
                continue
            test_sa = metric.value("RotD(percentile=50.0)")
            np.testing.assert_allclose(test_sa, 53.133845)

    streams = ws.get_streams("ci38457511", labels=["default"])
    event = ws.get_event("ci38457511")
    config = ws.config
    config["metrics"] = {
        "components_and_types": {
            "channels": ["pga", "sa"],
            "geometric_mean": ["pga", "sa"],
            "rotd": ["sa"],
        },
        "type_parameters": {
            "sa": {
                "damping": [0.05],
                "periods": [0.5, 1.0],
            },
        },
        "component_parameters": {
            "rotd": {
                "percentiles": [50.0],
            },
        },
    }
    wmc2 = WaveformMetricCollection.from_streams(streams, event, config)
    assert wmc2.__repr__() == "WaveformMetricCollection: 3 stations"
    for wml, sp in zip(wmc2.waveform_metrics, wmc2.stream_paths):
        if sp.startswith("CI.CCC"):
            for metric in wml.metric_list:
                if metric.type != "SA":
                    continue
                if metric.metric_attributes["period"] != 1.0:
                    continue
                mdict = metric.to_dict()
                idx = np.where(
                    np.array(mdict["components"]) == "RotD(percentile=50.0)"
                )[0]
                test_sa = np.array(mdict["values"])[idx][0]
                np.testing.assert_allclose(test_sa, 53.133845)
