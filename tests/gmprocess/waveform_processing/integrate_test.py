import copy

import numpy as np

from gmprocess.waveform_processing.integrate import get_disp, get_vel


def test_get_disp(load_data_us1000778i, config):
    conf = copy.deepcopy(config)
    sc, _ = load_data_us1000778i
    sc = sc.copy()

    conf["integration"]["frequency"] = True

    final_disp = []
    for st in sc:
        for tr in st:
            tmp_tr = get_disp(tr, config=conf)
            final_disp.append(tmp_tr.data[-1])

    target_final_disp = np.array(
        [-3.757783948454829e-05, -6.270737408442528e-06, -1.059570751504868e-05]
    )
    np.testing.assert_allclose(final_disp, target_final_disp, atol=1e-6)

    conf["integration"]["frequency"] = False
    conf["integration"]["initial"] = 0.0
    conf["integration"]["demean"] = True

    final_disp = []
    for st in sc:
        for tr in st:
            tmp_tr = get_disp(tr, config=conf)
            final_disp.append(tmp_tr.data[-1])

    target_final_disp = np.array(
        [-2.462690027204846, -0.41095702523173544, -0.6943951449700738]
    )
    np.testing.assert_allclose(final_disp, target_final_disp, atol=1e-6, rtol=1e-04)


def test_get_vel(load_data_us1000778i, config):
    conf = copy.deepcopy(config)
    sc, _ = load_data_us1000778i
    sc = sc.copy()

    conf["integration"]["frequency"] = True

    final_vel = []
    for st in sc:
        for tr in st:
            tmp_tr = get_vel(tr, config=conf)
            final_vel.append(tmp_tr.data[-1])

    target_final_vel = np.array(
        [2.386161152612143e-06, -3.1275235786720756e-06, -6.3198991595569964e-09]
    )

    np.testing.assert_allclose(final_vel, target_final_vel, atol=1e-6)


def test_integrate_taper(load_data_us1000778i, config):
    conf = copy.deepcopy(config)
    sc, _ = load_data_us1000778i
    sc = sc.copy()

    conf["integration"]["taper"] = True

    final_vel = []
    for st in sc:
        for tr in st:
            tmp_tr = tr.integrate(**conf["integration"])
            final_vel.append(tmp_tr.data[-1])

    target_final_vel = np.array(
        [2.386161152612143e-06, -3.1275235786720756e-06, -6.3198991595569964e-09]
    )

    np.testing.assert_allclose(final_vel, target_final_vel, atol=1e-6)
