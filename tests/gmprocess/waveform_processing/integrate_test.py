import numpy as np
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
            -3.132284e-03,
            3.236543e-03,
            -1.151739e-03,
            -3.757784e-05,
            -6.270737e-06,
            -1.059571e-05,
            -1.020162e-04,
            7.182205e-06,
            -2.245060e-06,
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
            -2.052774e02,
            2.121101e02,
            -7.548038e01,
            -2.462690e00,
            -4.109570e-01,
            -6.943951e-01,
            -6.039364e00,
            4.251883e-01,
            -1.329093e-01,
        ]
    )

    np.testing.assert_allclose(final_disp, target_final_disp, atol=1e-6, rtol=1e-04)


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
            5.948475e-05,
            -7.475819e-05,
            -8.651218e-06,
            2.386161e-06,
            -3.127524e-06,
            -6.319899e-09,
            6.127922e-07,
            3.791711e-06,
            1.649075e-06,
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
            5.948475e-05,
            -7.475819e-05,
            -8.651218e-06,
            2.386161e-06,
            -3.127524e-06,
            -6.319899e-09,
            6.127922e-07,
            3.791711e-06,
            1.649075e-06,
        ]
    )

    np.testing.assert_allclose(final_vel, target_final_vel, atol=1e-6)
