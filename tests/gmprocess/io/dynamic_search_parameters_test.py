import numpy as np

from gmprocess.io.dynamic_search_parameters import SearchParameters
from gmprocess.utils.config import get_config
from gmprocess.utils.strec import STREC
from gmprocess.utils.constants import TEST_DATA_DIR


def test_dynamic_search_parameters():
    config = get_config()

    # ACR
    strec = STREC.from_file(TEST_DATA_DIR / "strec_results_nc73774300.json")
    magnitude = 4.0
    search_pars = SearchParameters(magnitude, config, strec)
    np.testing.assert_allclose(search_pars.distance, 15.85656901)
    np.testing.assert_allclose(search_pars.duration, 2.0)

    magnitude = 6.0
    search_pars = SearchParameters(magnitude, config, strec)
    np.testing.assert_allclose(search_pars.distance, 155.43615444)
    np.testing.assert_allclose(search_pars.duration, 3.0)

    # SRC
    strec = STREC.from_file(TEST_DATA_DIR / "strec_results_nm60363582.json")

    magnitude = 4.0
    search_pars = SearchParameters(magnitude, config, strec)
    np.testing.assert_allclose(search_pars.distance, 29.69809652)
    np.testing.assert_allclose(search_pars.duration, 2.0)

    magnitude = 6.0
    search_pars = SearchParameters(magnitude, config, strec)
    np.testing.assert_allclose(search_pars.distance, 258.71288089)
    np.testing.assert_allclose(search_pars.duration, 3.0)

    # No STREC, should match SRC
    strec = STREC.from_file(TEST_DATA_DIR / "strec_results_nm60363582.json")

    magnitude = 4.0
    search_pars = SearchParameters(magnitude, config, strec=None)
    np.testing.assert_allclose(search_pars.distance, 29.69809652)
    np.testing.assert_allclose(search_pars.duration, 2.0)

    magnitude = 6.0
    search_pars = SearchParameters(magnitude, config, strec)
    np.testing.assert_allclose(search_pars.distance, 258.71288089)
    np.testing.assert_allclose(search_pars.duration, 3.0)