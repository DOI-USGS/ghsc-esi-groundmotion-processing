import copy

import numpy as np

from gmprocess.metrics.waveform_metric_calculator import WaveformMetricCalculator
from gmprocess.metrics.utils import component_to_channel
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.utils import constants


def test_get_channel_dict():
    channel_names1 = ["HNN", "HNE", "HNZ"]
    cdict, _ = component_to_channel(channel_names1)
    assert sorted(cdict.keys()) == ["H1", "H2", "Z"]

    channel_names2 = ["HN1", "HN2", "HNZ"]
    cdict, _ = component_to_channel(channel_names2)
    assert sorted(cdict.keys()) == ["H1", "H2", "Z"]

    channel_names3 = ["HN1", "HNE", "HNZ"]
    cdict, _ = component_to_channel(channel_names3)
    assert sorted(cdict.keys()) == ["H1", "H2", "Z"]

    channel_names4 = ["HN1", "HNZ"]
    cdict, _ = component_to_channel(channel_names4)
    assert sorted(cdict.keys()) == ["H1", "Z"]

    channel_names5 = ["HN2", "HN3", "HNZ"]
    cdict, _ = component_to_channel(channel_names5)
    assert sorted(cdict.keys()) == ["H1", "H2", "Z"]

    channel_names6 = ["HN2", "HN3"]
    cdict, _ = component_to_channel(channel_names6)
    assert sorted(cdict.keys()) == ["H1", "H2"]

    channel_names7 = ["HN2", "HNZ"]
    cdict, _ = component_to_channel(channel_names7)
    assert sorted(cdict.keys()) == ["H1", "Z"]

    channel_names8 = ["HN2"]
    cdict, _ = component_to_channel(channel_names8)
    assert sorted(cdict.keys()) == ["H1"]

    channel_names9 = ["HN1"]
    cdict, _ = component_to_channel(channel_names9)
    assert sorted(cdict.keys()) == ["H1"]

    channel_names10 = ["HNZ"]
    cdict, _ = component_to_channel(channel_names10)
    assert sorted(cdict.keys()) == ["Z"]


def test_metric_calculator(config):
    event_dir = constants.TEST_DATA_DIR / "waveform_metric_calculator" / "nc72282711"
    ws = StreamWorkspace(event_dir / "workspace.h5")
    streams = ws.get_streams(event_id="nc72282711", labels=["default"])
    conf = copy.deepcopy(config)

    metric_config = {
        "components_and_types": {
            "channels": [
                "pga",
                "pgv",
                "psa",
                "sa",
                "psv",
                "sv",
                "sd",
                "arias",
                "cav",
                "duration",
            ],
            "arithmetic_mean": ["pga", "pgv", "sa", "arias", "cav", "duration"],
            "geometric_mean": ["pga", "pgv", "sa", "arias", "cav", "duration"],
            "quadratic_mean": ["fas"],
            "rotd": ["pga", "pgv", "psa", "sa", "psv", "sv", "sd"],
        },
        "type_parameters": {
            "sa": {
                "damping": [0.05, 0.1],
                "periods": [0.3, 1.0, 2.0],
            },
            "sv": {
                "damping": [0.05, 0.1],
                "periods": [0.3, 1.0, 2.0],
            },
            "sd": {
                "damping": [0.05, 0.1],
                "periods": [0.3, 1.0, 2.0],
            },
            "fas": {
                "smoothing_method": "konno_ohmachi",
                "smoothing_parameter": 20.0,
                "allow_nans": True,
                "frequencies": {
                    "start": 0.001,
                    "stop": 100.0,
                    "num": 401,
                },
            },
            "duration": {
                "intervals": ["5-75", "5-95"],
            },
        },
        "component_parameters": {
            "rotd": {
                "percentiles": [50.0, 100.0],
            }
        },
    }

    conf["metrics"] = metric_config

    # Trim stream to limit memory usage in unit tests
    stream = streams[0]
    start_time = stream[0].stats.starttime
    stream.trim(endtime=start_time + 50)

    wm_calc = WaveformMetricCalculator(stream, conf)
    wml = wm_calc.calculate()

    pga = wml.select("PGA")[0].values
    np.testing.assert_allclose(pga["Channels(component=H1)"], 1.7931487464243818)
    np.testing.assert_allclose(pga["Channels(component=H2)"], 6.785188430936665)
    np.testing.assert_allclose(pga["RotD(percentile=50.0)"], 4.866262570206258)
    np.testing.assert_allclose(pga["RotD(percentile=100.0)"], 6.888672765758448)

    pgv = wml.select("PGV")[0].values
    np.testing.assert_allclose(pgv["Channels(component=H1)"], 2.163067423847448)
    np.testing.assert_allclose(pgv["Channels(component=H2)"], 4.256087648335906)
    np.testing.assert_allclose(pgv["RotD(percentile=50.0)"], 3.183163677079098)
    np.testing.assert_allclose(pgv["RotD(percentile=100.0)"], 4.5218794245674445)

    sa1 = wml.select("SA", period=1.0, damping=0.05)[0].values
    np.testing.assert_allclose(sa1["Channels(component=H1)"], 1.7828037195911188)
    np.testing.assert_allclose(sa1["Channels(component=H2)"], 4.416147088914179)
    np.testing.assert_allclose(sa1["RotD(percentile=50.0)"], 3.2229970792851685)
    np.testing.assert_allclose(sa1["RotD(percentile=100.0)"], 4.462208189809311)

    psa1 = wml.select("PSA", period=1.0, damping=0.05)[0].values
    np.testing.assert_allclose(psa1["Channels(component=H1)"], 1.7670537119030583)
    np.testing.assert_allclose(psa1["Channels(component=H2)"], 4.42307246601832)
    np.testing.assert_allclose(psa1["RotD(percentile=50.0)"], 3.175834145860264)
    np.testing.assert_allclose(psa1["RotD(percentile=100.0)"], 4.4586520481240095)

    sv1 = wml.select("SV", period=1.0, damping=0.05)[0].values
    np.testing.assert_allclose(sv1["Channels(component=H1)"], 2.431155211678591)
    np.testing.assert_allclose(sv1["Channels(component=H2)"], 6.9209408886077215)
    np.testing.assert_allclose(sv1["RotD(percentile=50.0)"], 5.175672456836995)
    np.testing.assert_allclose(sv1["RotD(percentile=100.0)"], 6.945663284696031)

    psv1 = wml.select("PSV", period=1.0, damping=0.05)[0].values
    np.testing.assert_allclose(psv1["Channels(component=H1)"], 2.757976477955058)
    np.testing.assert_allclose(psv1["Channels(component=H2)"], 6.90342898996068)
    np.testing.assert_allclose(psv1["RotD(percentile=50.0)"], 4.956768327509457)
    np.testing.assert_allclose(psv1["RotD(percentile=100.0)"], 6.9589607770716)

    sd1 = wml.select("SD", period=1.0, damping=0.05)[0].values
    np.testing.assert_allclose(sd1["Channels(component=H1)"], 0.4389455893977232)
    np.testing.assert_allclose(sd1["Channels(component=H2)"], 1.0987148480361326)
    np.testing.assert_allclose(sd1["RotD(percentile=50.0)"], 0.788894181084477)
    np.testing.assert_allclose(sd1["RotD(percentile=100.0)"], 1.1075530064535624)

    fas = wml.select("FAS")[0].values
    fas_qm = fas["QuadraticMean()"]
    np.testing.assert_allclose(
        fas_qm.frequency[:2], np.array([0.001, 0.0010292005271944286])
    )
    np.testing.assert_allclose(fas_qm.fourier_spectra[0], np.nan)
    np.testing.assert_allclose(fas_qm.fourier_spectra[120], 0.5730162282115605)
    np.testing.assert_allclose(fas_qm.fourier_spectra[240], 9.20927159643677)
