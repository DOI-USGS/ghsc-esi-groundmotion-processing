import copy

import numpy as np

from gmprocess.io.dynamic_search_parameters import SearchParameters
from gmprocess.utils.strec import STREC
from gmprocess.utils.constants import TEST_DATA_DIR


def test_dynamic_search_parameters(config):
    conf = copy.deepcopy(config)

    # ACR
    strec = STREC.from_file(TEST_DATA_DIR / "strec_results_nc73774300.json")
    magnitude = 4.0
    search_pars = SearchParameters(magnitude, conf, strec)
    np.testing.assert_allclose(search_pars.distance, 204.424387)
    np.testing.assert_allclose(search_pars.duration, 2.0)

    magnitude = 6.0
    search_pars = SearchParameters(magnitude, conf, strec)
    np.testing.assert_allclose(search_pars.distance, 587.301345)
    np.testing.assert_allclose(search_pars.duration, 3.0)

    # SRC
    strec = STREC.from_file(TEST_DATA_DIR / "strec_results_nm60363582.json")

    magnitude = 4.0
    search_pars = SearchParameters(magnitude, conf, strec)
    np.testing.assert_allclose(search_pars.distance, 576.576225)
    np.testing.assert_allclose(search_pars.duration, 2.0)

    magnitude = 6.0
    search_pars = SearchParameters(magnitude, conf, strec)
    np.testing.assert_allclose(search_pars.distance, 800.0)
    np.testing.assert_allclose(search_pars.duration, 3.0)

    # No STREC, should match SRC
    strec = STREC.from_file(TEST_DATA_DIR / "strec_results_nm60363582.json")

    magnitude = 4.0
    search_pars = SearchParameters(magnitude, conf, strec=None)
    np.testing.assert_allclose(search_pars.distance, 576.576225)
    np.testing.assert_allclose(search_pars.duration, 2.0)

    magnitude = 6.0
    search_pars = SearchParameters(magnitude, conf, strec)
    np.testing.assert_allclose(search_pars.distance, 800.0)
    np.testing.assert_allclose(search_pars.duration, 3.0)
