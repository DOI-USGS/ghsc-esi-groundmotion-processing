"""Utilities for the metrics package."""

import re


def component_to_channel(channel_names):
    """Dictionary with mapping from channel name to component.

    Args:
        channel_names (list):
            List of strings for channel names, e.g., ["HNZ", "HNN", "HNE"].
    """
    channel_names = sorted(channel_names)
    channel_dict = {}
    reverse_dict = {}
    channel_number = 1
    for channel_name in channel_names:
        if channel_name.endswith("Z"):
            channel_dict["Z"] = channel_name
        else:
            cname = "H%i" % channel_number
            channel_number += 1
            channel_dict[cname] = channel_name

    reverse_dict = {v: k for k, v in channel_dict.items()}
    return (channel_dict, reverse_dict)


def parse_period(imt):
    """
    Parses the period from the imt.

    Args:
        imt (string):
            Imt that contains a period similar to one of the following
            examples:
                - SA(1.0)
                - SA(1)
                - SA1.0
                - SA1
    Returns:
        str: Period for the calculation.

    Notes:
        Can be either a float or integer.
    """
    period = re.findall(r"\d+", imt)

    if len(period) > 1:
        period = ".".join(period)
    elif len(period) == 1:
        period = period[0]
    else:
        period = None
    return period


def parse_percentile(imc):
    """
    Parses the percentile from the imc.

    Args:
        imc (string):
            Imc that contains a period similar to one of the following
            examples:
                - ROTD(50.0)
                - ROTD(50)
                - ROTD50.0
                - ROTD50

    Returns:
        str: Period for the calculation.

    Notes:
        Can be either a float or integer.
    """
    percentile = re.findall(r"\d+", imc)
    if len(percentile) > 1:
        percentile = ".".join(percentile)
    elif len(percentile) == 1:
        percentile = percentile[0]
    else:
        percentile = None
    return percentile


def parse_interval(imt):
    """
    Parses the interval from the imt string.

    Args:
        imt (string):
            Imt that contains a interval.
            example:
                - duration5-95
    Returns:
        str: Interval for the calculation.

    Notes:
        Can be either a float or integer.
    """
    tmpstr = imt.replace("duration", "")
    if tmpstr:
        return [int(p) for p in tmpstr.split("-")]
    else:
        return None


def find_float(imt):
    """Find the float in an IMT string.

    Args:
        imt (str):
            An IMT string with a float in it (e.g., period for SA).

    Returns:
        float: the IMT float, if found, otherwise None.
    """
    try:
        return float(re.search(r"[0-9]*\.[0-9]*", imt).group())
    except AttributeError:
        return None
