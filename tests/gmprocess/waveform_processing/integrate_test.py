import numpy as np
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.io.read import read_data
from gmprocess.utils.tests_utils import read_data_dir
from gmprocess.waveform_processing.integrate import get_disp, get_vel
from gmprocess.utils.config import get_config


def test_get_disp(geonet_uncorrected_waveforms):
    sc, _ = geonet_uncorrected_waveforms

    config = get_config()
    config["integration"]["frequency"] = True

    final_disp = []
    for st in sc:
        for tr in st:
            tmp_tr = get_disp(tr, config=config)
            final_disp.append(tmp_tr.data[-1])

    target_final_disp = np.array(
        [
            -0.07689,
            0.082552,
            -0.024509,
            -0.00047,
            -0.000257,
            -0.000152,
            -0.003425,
            0.000671,
            0.000178,
        ]
    )

    np.testing.assert_allclose(final_disp, target_final_disp, atol=1e-6)

    config["integration"]["frequency"] = False
    config["integration"]["initial"] = 0.0
    config["integration"]["demean"] = True

    final_disp = []
    for st in sc:
        for tr in st:
            tmp_tr = get_disp(tr, config=config)
            final_disp.append(tmp_tr.data[-1])

    target_final_disp = np.array(
        [
            -0.076882,
            0.082549,
            -0.024512,
            -0.000469,
            -0.000259,
            -0.000152,
            -0.003425,
            0.000672,
            0.000178,
        ]
    )

    np.testing.assert_allclose(final_disp, target_final_disp, atol=1e-6)


def test_get_vel(geonet_uncorrected_waveforms):
    sc, _ = geonet_uncorrected_waveforms

    config = get_config()
    config["integration"]["frequency"] = True

    final_vel = []
    for st in sc:
        for tr in st:
            tmp_tr = get_vel(tr, config=config)
            final_vel.append(tmp_tr.data[-1])

    target_final_vel = np.array(
        [
            -2.182293e-03,
            -1.417545e-03,
            2.111492e-03,
            -9.395322e-04,
            1.662219e-03,
            -2.690978e-04,
            1.376186e-04,
            -7.358185e-05,
            1.741465e-05,
        ]
    )

    np.testing.assert_allclose(final_vel, target_final_vel, atol=1e-6)


def test_integrate_taper(geonet_uncorrected_waveforms):
    sc, _ = geonet_uncorrected_waveforms

    config = get_config()
    config["integration"]["taper"] = True

    final_vel = []
    for st in sc:
        for tr in st:
            tmp_tr = tr.integrate(**config["integration"])
            final_vel.append(tmp_tr.data[-1])

    target_final_vel = np.array(
        [
            5.952099e-05,
            -7.481835e-05,
            -8.635273e-06,
            2.430373e-06,
            -2.758605e-06,
            -2.371486e-08,
            -3.067016e-07,
            2.616267e-06,
            1.683576e-06,
        ]
    )

    np.testing.assert_allclose(final_vel, target_final_vel, atol=1e-6)
