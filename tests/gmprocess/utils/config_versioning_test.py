from ruamel.yaml import YAML

from gmprocess.utils.constants import DATA_DIR
from gmprocess.utils.config_versioning import get_config_version, config_from_v1


def test_config_from_v1():
    conf_v1_file = DATA_DIR / "config_production_v1.yml"
    with open(conf_v1_file, "r", encoding="utf-8") as f:
        yaml = YAML()
        yaml.preserve_quotes = True
        conf_v1 = yaml.load(f)
    config_from_v1(conf_v1)


def test_get_config_version():
    conf_v1_file = DATA_DIR / "config_production_v1.yml"
    with open(conf_v1_file, "r", encoding="utf-8") as f:
        yaml = YAML()
        yaml.preserve_quotes = True
        conf_v1 = yaml.load(f)
    conf_v2_file = DATA_DIR / "config_production.yml"
    with open(conf_v2_file, "r", encoding="utf-8") as f:
        yaml = YAML()
        yaml.preserve_quotes = True
        conf_v2 = yaml.load(f)

    assert get_config_version(conf_v1) == 1
    assert get_config_version(conf_v2) == 2
