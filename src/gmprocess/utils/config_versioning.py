"""Module for handling config versioning issues.

Note: This needs to be a separate module from config.py because we need to import
WaveformMetricCalculator, which would create a circular import since it imports 
gmprocess.metrics.containers, which imports gmprocess.utils.config.
"""

import logging

import numpy as np
from ruamel.yaml import YAML

from gmprocess.utils import constants
from gmprocess.metrics.waveform_metric_calculator import WaveformMetricCalculator
from gmprocess.utils.config import CONF_SCHEMA


def get_config_version(conf_dict):
    """Determine the config version.

    Args:
        conf_dict (dict):
            Dictionary of config options.
    """
    if "version" in conf_dict:
        return conf_dict["version"]
    else:
        return 1


def config_from_v1(conf_dict):
    """Convert from v1 to v2 config.

    Args:
        conf_dict (dict):
            Dictionary of config options.
    """
    default_config_file = constants.DATA_DIR / constants.CONFIG_FILE_PRODUCTION
    if not default_config_file.exists():
        fmt = "Missing config file: %s."
        raise OSError(fmt % default_config_file)
    else:
        with open(default_config_file, "r", encoding="utf-8") as f:
            yaml = YAML()
            yaml.preserve_quotes = True
            default_config = yaml.load(f)

    # reorganize metrics section
    old_metrics = conf_dict.pop("metrics")

    new_metrics = {
        "components_and_types": {},
        "component_parameters": {},
        "type_parameters": {"sa": {}, "fas": {}, "duration": {}},
    }
    old_imcs = old_metrics["output_imcs"]
    old_imts = old_metrics["output_imts"]
    rotd_percentiles = []
    for old_imc in old_imcs:
        old_imc = old_imc.lower()
        if old_imc == "rotd50":
            rotd_percentiles.append(50.0)
            old_imc = "rotd"
        for old_imt in old_imts:
            old_imt = old_imt.lower()
            im_str = f"{old_imc}-{old_imt}"
            if im_str in WaveformMetricCalculator.all_steps:
                if old_imc not in new_metrics["components_and_types"]:
                    new_metrics["components_and_types"][old_imc] = []
                new_metrics["components_and_types"][old_imc].append(old_imt)

    new_metrics["component_parameters"]["rotd"] = {"percentiles": rotd_percentiles}

    # Only supported one damping value previously
    new_metrics["type_parameters"]["sa"]["damping"] = [old_metrics["sa"]["damping"]]

    # Now, only support period array for SA
    if old_metrics["sa"]["periods"]["use_array"]:
        start = old_metrics["sa"]["periods"]["start"]
        stop = old_metrics["sa"]["periods"]["stop"]
        num = old_metrics["sa"]["periods"]["num"]
        if old_metrics["sa"]["periods"]["spacing"] == "logspace":
            new_periods = np.logspace(np.log10(start), np.log10(stop), num=num)
        else:
            new_periods = np.linspace(start, stop, num=num)
    else:
        new_periods = old_metrics["sa"]["periods"]["defined_periods"]
    new_metrics["type_parameters"]["sa"]["periods"] = new_periods

    # The only smoothing method has always been konno_ohmachi
    new_metrics["type_parameters"]["fas"]["smoothing_method"] = "konno_ohmachi"
    new_metrics["type_parameters"]["fas"]["smoothing_parameter"] = old_metrics["fas"][
        "bandwidth"
    ]
    new_metrics["type_parameters"]["fas"]["allow_nans"] = old_metrics["fas"][
        "allow_nans"
    ]
    logging.warning(
        "Cannot convert old FAS frequency/period values and they will be overwritten "
        "with new defaults"
    )
    new_metrics["type_parameters"]["fas"]["frequencies"] = {
        "start": 0.001,
        "stop": 100.0,
        "num": 401,
    }

    new_metrics["type_parameters"]["duration"]["intervals"] = old_metrics["duration"][
        "intervals"
    ]

    conf_dict["metrics"] = new_metrics

    if "integration" in conf_dict:
        old_integration = conf_dict.pop("integration")
        new_integration = {
            "frequency": old_integration["frequency"],
            "initial": old_integration["initial"],
            "demean": old_integration["demean"],
            "taper": old_integration["taper"]["taper"],
            "taper_width": old_integration["taper"]["width"],
            "taper_type": old_integration["taper"]["type"],
            "taper_side": old_integration["taper"]["side"],
        }
        conf_dict["integration"] = new_integration
    else:
        conf_dict["integration"] = default_config["integration"]

    if "search_parameters" not in conf_dict["fetchers"]:
        conf_dict["fetchers"]["search_parameters"] = default_config["fetchers"][
            "search_parameters"
        ]
        conf_dict["fetchers"]["search_parameters"]["enabled"] = False

    for _, fetcher_dict in conf_dict["fetchers"].items():
        if "enabled" not in fetcher_dict:
            fetcher_dict["enabled"] = False

    fdsn_section = conf_dict["fetchers"]["FDSNFetcher"]

    if "radius" in fdsn_section:
        fdsn_section["domain"] = default_config["fetchers"]["FDSNFetcher"]["domain"]
        fdsn_section["domain"]["circular"]["maxradius"] = fdsn_section.pop("radius")
    restriction_keys = [
        "time_before",
        "time_after",
        "channels",
        "exclude_patterns",
        "network",
        "exclude_networks",
        "reject_channels_with_gaps",
        "minimum_length",
        "sanitize",
        "minimum_interstation_distance_in_m",
    ]
    if "restrictions" not in fdsn_section:
        fdsn_section["restrictions"] = default_config["fetchers"]["FDSNFetcher"][
            "restrictions"
        ]
    for restriction_key in restriction_keys:
        if restriction_key in fdsn_section:
            if restriction_key == "channels":
                old_channels = fdsn_section.pop(restriction_key)
                fdsn_section["restrictions"]["channel"] = ",".join(old_channels)
            elif restriction_key == "exclude_patterns":
                conf_dict["read"][restriction_key] = fdsn_section.pop(restriction_key)
            else:
                fdsn_section["restrictions"][restriction_key] = fdsn_section.pop(
                    restriction_key
                )

    if "providers" not in fdsn_section:
        fdsn_section["providers"] = default_config["fetchers"]["FDSNFetcher"][
            "providers"
        ]

    if "TurkeyFetcher" in conf_dict["fetchers"]:
        conf_dict["fetchers"].pop("TurkeyFetcher")

    if "use_streamcollection" not in conf_dict["read"]:
        conf_dict["read"]["use_streamcollection"] = True

    if "no_noise" not in conf_dict["windows"]:
        conf_dict["windows"]["no_noise"] = False

    wc_section = conf_dict["windows"]["window_checks"]
    if "do_check" in wc_section:
        wc_section["enabled"] = conf_dict["windows"]["window_checks"].pop("do_check")

    if "enabled" not in conf_dict["colocated"]:
        conf_dict["colocated"]["enabled"] = True
    if "large_dist" not in conf_dict["colocated"]:
        conf_dict["colocated"]["large_dist"] = default_config["colocated"]["large_dist"]
        conf_dict["colocated"]["large_dist"]["enabled"] = False
    else:
        lg_section = conf_dict["colocated"]["large_dist"]
        if "enabled" not in lg_section:
            lg_section["enabled"] = True

    if "enabled" not in conf_dict["build_report"]:
        conf_dict["build_report"]["enabled"] = True

    pickers_add = {
        "p_arrival_shift": -2.0,
        "methods": ["travel_time", "ar", "baer", "power", "kalkan"],
        "window": 10.0,
        "combine": "median",
        "pick_travel_time_warning": 3.0,
        "plot_picks": False,
    }
    conf_dict["pickers"].update(pickers_add)



    # Possible full replacements
    replace_sections = [
        "check_stream",
        "differentiation",
        "error_notification",
        "gmm_selection",
        "strec",
    ]
    for replace_section in replace_sections:
        if replace_section not in conf_dict:
            conf_dict[replace_section] = default_config[replace_section]

    conf_dict["version"] = 2

    if "user" not in conf_dict:
        conf_dict["user"] = {"name": "unknown", "email": "unknown"}

    CONF_SCHEMA.validate(conf_dict)

    return conf_dict
