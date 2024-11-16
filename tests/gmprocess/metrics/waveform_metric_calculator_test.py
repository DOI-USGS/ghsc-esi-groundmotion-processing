import copy

import numpy as np

from gmprocess.metrics.waveform_metric_calculator import WaveformMetricCalculator
from gmprocess.metrics.utils import component_to_channel


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


def test_metric_calculator(load_data_us1000778i, config):
    streams, _ = load_data_us1000778i
    streams = streams.copy()
    conf = copy.deepcopy(config)

    metric_config = {
        "components_and_types": {
            "channels": ["pga", "pgv", "sa", "sv", "sd", "arias", "cav", "duration"],
            "arithmetic_mean": ["pga", "pgv", "sa", "arias", "cav", "duration"],
            "geometric_mean": ["pga", "pgv", "sa", "arias", "cav", "duration"],
            "quadratic_mean": ["fas"],
            "rotd": ["pga", "pgv", "sa", "sv", "sd"],
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

    stream = streams[0]

    wm_calc = WaveformMetricCalculator(stream, conf)
    wml = wm_calc.calculate()

    pga = wml.select("PGA")[0].values
    np.testing.assert_allclose(pga["Channels(component=H1)"], 24.420163868395427)
    np.testing.assert_allclose(pga["Channels(component=H2)"], 26.353545808201577)
    np.testing.assert_allclose(pga["Channels(component=Z)"], 16.212468070136083)
    np.testing.assert_allclose(pga["RotD(percentile=50.0)"], 26.13784399742242)
    np.testing.assert_allclose(pga["RotD(percentile=100.0)"], 27.490172337334727)

    pgv = wml.select("PGV")[0].values
    np.testing.assert_allclose(pgv["Channels(component=H1)"], 32.01422425132747)
    np.testing.assert_allclose(pgv["Channels(component=H2)"], 33.217128830523485)
    np.testing.assert_allclose(pgv["Channels(component=Z)"], 13.668950711224722)
    np.testing.assert_allclose(pgv["RotD(percentile=50.0)"], 31.479009225758396)
    np.testing.assert_allclose(pgv["RotD(percentile=100.0)"], 33.315065646041774)

    sa1 = wml.select("SA", period=1.0, damping=0.05)[0].values
    np.testing.assert_allclose(sa1["Channels(component=H1)"], 42.135839214645564)
    np.testing.assert_allclose(sa1["Channels(component=H2)"], 41.891393940234074)
    np.testing.assert_allclose(sa1["Channels(component=Z)"], 12.789046181803089)
    np.testing.assert_allclose(sa1["RotD(percentile=50.0)"], 42.13583921464555)
    np.testing.assert_allclose(sa1["RotD(percentile=100.0)"], 47.910999673071736)

    sv1 = wml.select("SV", period=1.0, damping=0.05)[0].values
    np.testing.assert_allclose(sv1["Channels(component=H1)"], 63.02799719)
    np.testing.assert_allclose(sv1["Channels(component=H2)"], 62.15551237)
    np.testing.assert_allclose(sv1["Channels(component=Z)"], 20.49380808)

    sd1 = wml.select("SD", period=1.0, damping=0.05)[0].values
    np.testing.assert_allclose(sd1["Channels(component=H1)"], 10.42514)
    np.testing.assert_allclose(sd1["Channels(component=H2)"], 10.35811174)
    np.testing.assert_allclose(sd1["Channels(component=Z)"], 3.15898147)

    fas = wml.select("FAS")[0].values
    fas_qm = fas["QuadraticMean()"]
    np.testing.assert_allclose(
        fas_qm.frequency[:2], np.array([0.001, 0.0010292005271944286])
    )
    np.testing.assert_allclose(fas_qm.fourier_spectra[0], np.nan)
    np.testing.assert_allclose(fas_qm.fourier_spectra[60], 0.9514159216822253)
    np.testing.assert_allclose(fas_qm.fourier_spectra[120], 5.121837741197534)
    np.testing.assert_allclose(fas_qm.fourier_spectra[240], 152.82217339085008)
