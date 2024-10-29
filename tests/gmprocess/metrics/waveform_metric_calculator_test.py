import numpy as np

from gmprocess.io.geonet.core import read_geonet
from gmprocess.metrics.waveform_metric_calculator import WaveformMetricCalculator
from gmprocess.metrics.utils import component_to_channel
from gmprocess.utils.config import get_config
from gmprocess.utils.constants import TEST_DATA_DIR

config = get_config()


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


def test_metric_calculator():
    config = get_config()
    metric_config = {
        "components_and_types": {
            "channels": ["pga", "pgv", "sa", "arias", "cav", "duration"],
            "arithmetic_mean": ["pga", "pgv", "sa", "arias", "cav", "duration"],
            "geometric_mean": ["pga", "pgv", "sa", "arias", "cav", "duration"],
            "quadratic_mean": ["fas"],
            "rotd": ["pga", "pgv", "sa"],
        },
        "type_parameters": {
            "sa": {
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
    config["metrics"] = metric_config
    datafile = TEST_DATA_DIR / "geonet" / "us1000778i/20161113_110259_WTMC_20.V2A"
    stream = read_geonet(datafile)[0]

    wm_calc = WaveformMetricCalculator(stream, config)
    wml = wm_calc.calculate()

    pga = wml.select("PGA")[0].values
    np.testing.assert_allclose(pga["Channels(component=H1)"], 99.24999872535474)
    np.testing.assert_allclose(pga["Channels(component=H2)"], 81.23467239067368)
    np.testing.assert_allclose(pga["Channels(component=Z)"], 183.7722361866693)
    np.testing.assert_allclose(pga["RotD(percentile=50.0)"], 91.40178541935455)
    np.testing.assert_allclose(pga["RotD(percentile=100.0)"], 100.73875535385548)

    pgv = wml.select("PGV")[0].values
    np.testing.assert_allclose(pgv["Channels(component=H1)"], 101.685117)
    np.testing.assert_allclose(pgv["Channels(component=H2)"], 68.6545070345289)
    np.testing.assert_allclose(pgv["Channels(component=Z)"], 39.51545299211966)
    np.testing.assert_allclose(pgv["RotD(percentile=50.0)"], 82.32464889631234)
    np.testing.assert_allclose(pgv["RotD(percentile=100.0)"], 114.80404091109193)

    sa1 = wml.select("SA", period=1.0, damping=0.05)[0].values
    np.testing.assert_allclose(sa1["Channels(component=H1)"], 136.25041187387063)
    np.testing.assert_allclose(sa1["Channels(component=H2)"], 84.69296738413021)
    np.testing.assert_allclose(sa1["Channels(component=Z)"], 27.74118995438756)
    np.testing.assert_allclose(sa1["RotD(percentile=50.0)"], 106.03202302692158)
    np.testing.assert_allclose(sa1["RotD(percentile=100.0)"], 146.9023350124098)

    fas = wml.select("FAS")[0].values
    fas_qm = fas["QuadraticMean()"]
    np.testing.assert_allclose(
        fas_qm.frequency[:2], np.array([0.001, 0.0010292005271944286])
    )
    np.testing.assert_allclose(fas_qm.fourier_spectra[0], np.nan)
    np.testing.assert_allclose(fas_qm.fourier_spectra[60], 0.054067101860127975)
    np.testing.assert_allclose(fas_qm.fourier_spectra[120], 0.056931415028755865)
    np.testing.assert_allclose(fas_qm.fourier_spectra[240], 229.7757904681393)
