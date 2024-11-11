import copy

from openquake.hazardlib.gsim.base import GMPE

from gmprocess.utils.ground_motion_models import load_model


def test_load_model(config):
    conf = copy.deepcopy(config)

    gmm_dict = conf["gmm_selection"]
    for _, gmm in gmm_dict.items():
        test_mod = load_model(gmm)
        assert isinstance(test_mod, GMPE)
