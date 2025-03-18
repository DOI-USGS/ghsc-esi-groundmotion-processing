"""Module for handling configuration options."""

import logging
import os

from ruamel.yaml import YAML
from schema import Optional, Or, Schema

from gmprocess.utils import constants

CONF_SCHEMA = Schema(
    {
        "version": int,
        "user": {"name": str, "email": str},
        "fetchers": {
            "search_parameters": {
                "enabled": bool,
                "duration": {
                    "c0": float,
                    "c1": float,
                    Optional("Stable"): {
                        "c0": float,
                        "c1": float,
                    },
                    Optional("Active"): {
                        "c0": float,
                        "c1": float,
                    },
                    Optional("Volcanic"): {
                        "c0": float,
                        "c1": float,
                    },
                    Optional("Subduction"): {
                        "c0": float,
                        "c1": float,
                    },
                },
                "distance": {"pga": float, "max_distance": float},
            },
            "KNETFetcher": {
                "user": str,
                "password": str,
                "radius": float,
                "dt": float,
                "ddepth": float,
                "dmag": float,
                "restrict_stations": bool,
                "enabled": bool,
            },
            "CESMDFetcher": {
                "email": str,
                "process_type": Or("raw", "processed"),
                "station_type": Or(
                    "Any",
                    "Array",
                    "Ground",
                    "Building",
                    "Bridge",
                    "Dam",
                    "Tunnel",
                    "Warf",
                    "Other",
                ),
                "eq_radius": float,
                "eq_dt": float,
                "station_radius": float,
                "enabled": bool,
            },
            "FDSNFetcher": {
                "enabled": bool,
                "domain": {
                    "type": Or("circular", "rectangular"),
                    "circular": {
                        "use_epicenter": bool,
                        Optional("latitude"): float,
                        Optional("longitude"): float,
                        "minradius": float,
                        "maxradius": float,
                    },
                    "rectangular": {
                        "minlatitude": float,
                        "maxlatitude": float,
                        "minlongitude": float,
                        "maxlongitude": float,
                    },
                },
                "restrictions": {
                    "time_before": float,
                    "time_after": float,
                    Optional("chunklength_in_sec"): float,
                    Optional("network"): str,
                    Optional("station"): str,
                    Optional("location"): str,
                    Optional("channel"): str,
                    Optional("exclude_networks"): list,
                    Optional("exclude_stations"): list,
                    Optional("reject_channels_with_gaps"): bool,
                    Optional("minimum_length"): float,
                    Optional("sanitize"): bool,
                    Optional("minimum_interstation_distance_in_m"): float,
                    Optional("channel_priorities"): list,
                    Optional("location_priorities"): list,
                },
                "providers": Or(None, list),
                Optional("authentication"): dict,
            },
        },
        "read": {
            "metadata_directory": str,
            "resample_rate": float,
            "sac_conversion_factor": float,
            "sac_source": str,
            "use_streamcollection": bool,
            "exclude_patterns": list,
        },
        "windows": {
            "no_noise": bool,
            "signal_end": {
                "method": Or("model", "source_path", "velocity", "magnitude", "none"),
                "model": str,
                "epsilon": float,
                "vmin": float,
                "floor": float,
                Optional("stress_drop", default=10.0): float,
                Optional("dur0", default=150.0): float,
                Optional("dur1", default=0.6): float,
                Optional("Regions"): {
                    Optional("Stable"): {
                        "method": Or(
                            "model", "source_path", "velocity", "magnitude", "none"
                        ),
                        "model": str,
                        "epsilon": float,
                        "vmin": float,
                        "floor": float,
                        "stress_drop": float,
                        "dur0": float,
                        "dur1": float,
                    },
                    Optional("Active"): {
                        "method": Or(
                            "model", "source_path", "velocity", "magnitude", "none"
                        ),
                        "model": str,
                        "epsilon": float,
                        "vmin": float,
                        "floor": float,
                        "stress_drop": float,
                        "dur0": float,
                        "dur1": float,
                    },
                    Optional("Volcanic"): {
                        "method": Or(
                            "model", "source_path", "velocity", "magnitude", "none"
                        ),
                        "model": str,
                        "epsilon": float,
                        "vmin": float,
                        "floor": float,
                        "stress_drop": float,
                        "dur0": float,
                        "dur1": float,
                    },
                    Optional("Subduction"): {
                        "method": Or(
                            "model", "source_path", "velocity", "magnitude", "none"
                        ),
                        "model": str,
                        "epsilon": float,
                        "vmin": float,
                        "floor": float,
                        "stress_drop": float,
                        "dur0": float,
                        "dur1": float,
                    },
                },
            },
            "window_checks": {
                "enabled": bool,
                "min_noise_duration": float,
                "min_signal_duration": float,
            },
        },
        "check_stream": {
            "any_trace_failures": bool,
        },
        "processing": list,
        "colocated": {
            "enabled": bool,
            "preference": list,
            "large_dist": {
                "enabled": bool,
                "preference": list,
                "mag": list,
                "dist": list,
            },
        },
        "duplicate": {
            "max_dist_tolerance": float,
            "preference_order": list,
            "process_level_preference": list,
            "format_preference": list,
        },
        "build_report": {"enabled": True, "format": "latex"},
        "metrics": {
            "components_and_types": dict,
            "type_parameters": {
                Optional("sa"): {
                    "damping": list,
                    "periods": list,
                },
                Optional("sv"): {
                    "damping": list,
                    "periods": list,
                },
                Optional("sd"): {
                    "damping": list,
                    "periods": list,
                },
                Optional("fas"): {
                    "smoothing_method": str,
                    "smoothing_parameter": float,
                    "allow_nans": bool,
                    "frequencies": {
                        "start": float,
                        "stop": float,
                        "num": int,
                    },
                },
                Optional("duration"): {"intervals": list},
            },
            Optional("component_parameters"): {"rotd": {"percentiles": list}},
        },
        "integration": {
            "frequency": bool,
            "initial": float,
            "demean": bool,
            "taper": bool,
            "taper_width": float,
            "taper_type": str,
            "taper_side": str,
        },
        "gmm_selection": {
            "ActiveShallow": str,
            "ActiveDeep": str,
            "VolcanicShallow": str,
            "SubductionIntraslab": str,
            "SubductionInterface": str,
            "SubductionCrustal": str,
            "StableShallow": str,
        },
        "differentiation": {
            "frequency": bool,
        },
        "pickers": {
            "p_arrival_shift": float,
            "methods": list,
            Optional("pick_travel_time_warning"): float,
            Optional("window"): float,
            Optional("combine"): Or("mean", "median", "max_snr"),
            Optional("plot_picks"): bool,
            "ar": {
                "f1": float,
                "f2": float,
                "lta_p": float,
                "sta_p": float,
                "lta_s": float,
                "sta_s": float,
                "m_p": int,
                "m_s": int,
                "l_p": float,
                "l_s": float,
                "s_pick": bool,
            },
            "baer": {
                "tdownmax": float,
                "tupevent": int,
                "thr1": float,
                "thr2": float,
                "preset_len": int,
                "p_dur": float,
            },
            "kalkan": {
                "period": Or("None", float),
                "damping": float,
                "nbins": Or("None", float),
                "peak_selection": bool,
            },
            "power": {
                "highpass": float,
                "lowpass": float,
                "order": int,
                "sta": float,
                "sta2": float,
                "lta": float,
                "hanningWindow": float,
                "threshDetect": float,
                "threshDetect2": float,
                "threshRestart": float,
            },
            "travel_time": {"model": str},
        },
        "error_notification": {
            "mail_host": Or(None, str),
            "subject": Or(None, str),
            "from_address": Or(None, str),
            "to_addresses": Or(None, str),
        },
        "strec": {"enabled": bool},
    }
)


def update_dict(target, source):
    """Merge values from source dictionary into target dictionary.

    Args:
        target (dict):
            Dictionary to be updated with values from source dictionary.

        source (dict):
            Dictionary with values to be transferred to target dictionary.
    """
    for key, value in source.items():
        if (
            not isinstance(value, dict)
            or key not in target.keys()
            or not isinstance(target[key], dict)
        ):
            target[key] = value
        else:
            update_dict(target[key], value)
    return


def merge_dicts(dicts):
    """Merges a list of dictionaries into a new dictionary.

    The order of the dictionaries in the list provides precedence of the
    values, with values from subsequent dictionaries overriding earlier
    ones.

    Args:
        dicts (list of dictionaries):
            List of dictionaries to be merged.

    Returns:
        dictionary: Merged dictionary.
    """
    target = dicts[0].copy()
    for source in dicts[1:]:
        update_dict(target, source)
    return target


def get_config(config_path=None):
    """Gets the user defined config and validates it.

    Args:
        config_path:
            pathlib.Path() object of directory containing config files to use. If None,
            uses defaults.

    Returns:
        dictionary:
            Configuration parameters.
    Raises:
        IndexError:
            If input section name is not found.
    """
    # Read in default config from the repository
    default_config_file = constants.DATA_DIR / constants.CONFIG_FILE_PRODUCTION
    if not default_config_file.exists():
        fmt = "Missing config file: %s."
        raise OSError(fmt % default_config_file)
    else:
        with open(default_config_file, "r", encoding="utf-8") as f:
            yaml = YAML()
            yaml.preserve_quotes = True
            default_config = yaml.load(f)
    # Add in fake user info so validation succeeds
    default_config["user"] = {"name": "NA", "email": "not@provided.com"}
    CONF_SCHEMA.validate(default_config)

    if config_path is None:
        logging.info("Using default config.")
        return default_config
    else:
        logging.info("Loading config from %s", config_path)
        config = __conf_path_to_config(config_path, default_config)

        return config


def update_config(custom_cfg_file, default_cfg):
    """Merge custom config with default.

    Args:
        custom_cfg_file (str):
            Path to custom config.
        default_cfg (dict):
            Default config file to be updated.

    Returns:
        dict: Merged config dictionary.

    """

    if not os.path.isfile(custom_cfg_file):
        return default_cfg
    with open(custom_cfg_file, "rt", encoding="utf-8") as f:
        yaml = YAML()
        yaml.preserve_quotes = True
        custom_cfg = yaml.load(f)
        update_dict(default_cfg, custom_cfg)

    return default_cfg


def __conf_path_to_config(config_path, default_config):
    conf_files = config_path.glob("**/*.yml")
    for cf in conf_files:
        default_config = update_config(cf, default_config)
    return default_config
