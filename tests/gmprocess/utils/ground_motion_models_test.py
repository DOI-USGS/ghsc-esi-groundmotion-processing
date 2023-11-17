from openquake.hazardlib.gsim.base import GMPE

from gmprocess.utils.ground_motion_models import load_model
from gmprocess.utils.config import get_config


def test_load_model():
    config = get_config()
    gmm_dict = config["gmm_selection"]
    for _, gmm in gmm_dict.items():
        print(gmm)
        test_mod = load_model(gmm)
        assert isinstance(test_mod, GMPE)
