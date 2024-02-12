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
            "geometric_mean": ["pga", "pgv", "sa", "arias", "cav", "duration"],
            "quadratic_mean": ["fas"],
            "rotd": ["pga", "pgv", "sa"],
        },
        "sa": {
            "damping": [0.05, 0.1],
            "periods": [0.3, 1.0, 2.0],
            "percentiles": [50.0, 100.0],
        },
        "fas": {
            "smoothing": "konno_ohmachi",
            "bandwidth": 20.0,
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
    }
    config["metrics"] = metric_config
    datafile = TEST_DATA_DIR / "geonet" / "us1000778i/20161113_110259_WTMC_20.V2A"
    stream = read_geonet(datafile)[0]

    wm_calc = WaveformMetricCalculator(stream, config)
    wm_calc.calculate()

    chan_pga = wm_calc.metric_dicts["channels-pga"][0]["result"].output.values
    for chan in chan_pga:
        if chan.stats.channel[2] == "1":
            h1_pga = chan.value
            h1_pga_time = chan.stats["peak_time"]
        elif chan.stats.channel[2] == "2":
            h2_pga = chan.value
            h2_pga_time = chan.stats["peak_time"]
        elif chan.stats.channel[2] == "Z":
            z_pga = chan.value
            z_pga_time = chan.stats["peak_time"]

    np.testing.assert_allclose(h1_pga, 99.24999872535474)
    np.testing.assert_allclose(h1_pga_time, 49.88)

    np.testing.assert_allclose(h2_pga, 81.23467239067368)
    np.testing.assert_allclose(h2_pga_time, 50.96)

    np.testing.assert_allclose(z_pga, 183.7722361866693)
    np.testing.assert_allclose(z_pga_time, 49.14)

    chan_pgv = wm_calc.metric_dicts["channels-pgv"][0]["result"].output.values
    for chan in chan_pgv:
        if chan.stats.channel[2] == "1":
            h1_pgv = chan.value
            h1_pgv_time = chan.stats["peak_time"]
        elif chan.stats.channel[2] == "2":
            h2_pgv = chan.value
            h2_pgv_time = chan.stats["peak_time"]
        elif chan.stats.channel[2] == "Z":
            z_pgv = chan.value
            z_pgv_time = chan.stats["peak_time"]

    np.testing.assert_allclose(h1_pgv, 101.66136239855638)
    np.testing.assert_allclose(h1_pgv_time, 51.58)

    np.testing.assert_allclose(h2_pgv, 68.64222974894496)
    np.testing.assert_allclose(h2_pgv_time, 49.86)

    np.testing.assert_allclose(z_pgv, 39.46762529609578)
    np.testing.assert_allclose(z_pgv_time, 50.56)

    rotd_pga = wm_calc.metric_dicts["rotd-pga"]
    for rotd in rotd_pga:
        if rotd["parameters"]["percentiles"] == 50.0:
            rotd50_pga = rotd["result"].output.value.value
        elif rotd["parameters"]["percentiles"] == 100.0:
            rotd100_pga = rotd["result"].output.value.value

    rotd_pgv = wm_calc.metric_dicts["rotd-pgv"]
    for rotd in rotd_pgv:
        if rotd["parameters"]["percentiles"] == 50.0:
            rotd50_pgv = rotd["result"].output.value.value
        elif rotd["parameters"]["percentiles"] == 100.0:
            rotd100_pgv = rotd["result"].output.value.value

    np.testing.assert_allclose(rotd50_pga, 91.40178541935455)
    np.testing.assert_allclose(rotd100_pga, 100.73875535385548)
    np.testing.assert_allclose(rotd50_pgv, 82.29808159181434)
    np.testing.assert_allclose(rotd100_pgv, 114.78926285861922)

    chan_sa = wm_calc.metric_dicts["channels-sa"]
    for chan in chan_sa:
        if chan["parameters"]["damping"] != 0.05:
            continue
        if chan["parameters"]["periods"] != 1.0:
            continue
        for ch in chan["result"].output.values:
            if ch.stats["channel"][2] == "1":
                h1_sa1 = ch.value
            elif ch.stats["channel"][2] == "2":
                h2_sa1 = ch.value
            elif ch.stats["channel"][2] == "Z":
                z_sa1 = ch.value

    np.testing.assert_allclose(h1_sa1, 136.25041187387063)
    np.testing.assert_allclose(h2_sa1, 84.69296738413021)
    np.testing.assert_allclose(z_sa1, 27.74118995438756)

    rotd_sa = wm_calc.metric_dicts["rotd-sa"]
    for rotd in rotd_sa:
        if rotd["parameters"]["damping"] != 0.05:
            continue
        if rotd["parameters"]["periods"] != 1.0:
            continue
        if rotd["parameters"]["percentiles"] == 50.0:
            rotd50_sa1 = rotd["result"].output.value.value
        if rotd["parameters"]["percentiles"] == 100.0:
            rotd100_sa1 = rotd["result"].output.value.value

    np.testing.assert_allclose(rotd50_sa1, 106.03202302692158)
    np.testing.assert_allclose(rotd100_sa1, 146.9023350124098)

    fas = wm_calc.metric_dicts["quadratic_mean-fas"][0]["result"].output
    np.testing.assert_allclose(
        fas.frequency[:2], np.array([0.001, 0.0010292005271944286])
    )
    np.testing.assert_allclose(fas.fourier_spectra[0], np.nan)
    np.testing.assert_allclose(fas.fourier_spectra[60], 0.054067101860127975)
    np.testing.assert_allclose(fas.fourier_spectra[120], 0.056931415028755865)
    np.testing.assert_allclose(fas.fourier_spectra[240], 229.7757904681393)
