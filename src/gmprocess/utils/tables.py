#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that provides functions for manipulating the various tables
(pandas DataFrames) produced by gmprocess.
"""

import re
import numpy as np

from gmprocess.utils.constants import TABLE_FLOAT_STRING_FORMAT


def set_precisions(df):
    """
    Sets the string format for float point number columns in the DataFrame.

    Args:
        df (pandas.DataFrame):
            Table for setting precision.

    Returns:
        pandas.DataFrame: The modified table.
    """

    # Create a copy so we're not modifying the original DF
    df = df.copy()
    for regex, str_format in TABLE_FLOAT_STRING_FORMAT.items():
        r = re.compile(regex, re.IGNORECASE)
        columns = list(filter(r.match, df.columns))
        for col in columns:
            df[col] = df[col].map(lambda x: str_format % x)
    return df


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


# Note: function is in this module to avoid a circular import.
def get_table_row(stream, summary, event, imc):
    tr = stream[0]
    base_station_id = ".".join([tr["network"], tr["station"], tr["location"]])
    if tr["use_array"]:
        station_id = ".".join([base_station_id, tr["channel"]])
    else:
        station_id = ".".join([base_station_id, tr["channel"][0:2]])

    if imc.lower() == "channels":
        if len(stream) > 1:
            raise ValueError("Stream must be length 1 to get row for imc=='channels'.")
        if not tr["passed"]:
            return {}
        lpf = tr["lowpass_filter"] if "lowpass_filter" in tr else np.nan
        hpf = tr["highpass_filter"] if "highpass_filter" in tr else np.nan
        filter_dict = {
            "Lowpass": lpf,
            "Highpass": hpf,
        }
        station_id = ".".join([base_station_id, tr["channel"]])
    elif imc == "Z":
        z = [tr for tr in stream if tr["channel"].endswith("Z")]
        if not len(z):
            return {}
        z = z[0]
        station_id = ".".join([base_station_id, z["channel"]])
        if not z["passed"]:
            return {}
        lpf = z["lowpass_filter"] if "lowpass_filter" in z else np.nan
        hpf = z["highpass_filter"] if "highpass_filter" in z else np.nan
        filter_dict = {
            "ZLowpass": lpf,
            "ZHighpass": hpf,
        }
    else:
        h1 = [tr for tr in stream if tr["channel"].endswith("1")]
        h2 = [tr for tr in stream if tr["channel"].endswith("2")]
        if not len(h1):
            h1 = [tr for tr in stream if tr["channel"].endswith("N")]
            h2 = [tr for tr in stream if tr["channel"].endswith("E")]

        # Return empty dict if no horizontal channels are found
        if not len(h1) or not len(h2):
            return {}

        h1 = h1[0]
        h2 = h2[0]

        # Return empty dict if the stream has not passed for the IMC requested
        if imc == "H1":
            if not h1["passed"]:
                return {}
            station_id = ".".join([base_station_id, h1["channel"]])
        if imc == "H2":
            if not h2["passed"]:
                return {}
            station_id = ".".join([base_station_id, h1["channel"]])
        h1lpf = h1["lowpass_filter"] if "lowpass_filter" in h1 else np.nan
        h1hpf = h1["highpass_filter"] if "highpass_filter" in h1 else np.nan
        h2lpf = h2["lowpass_filter"] if "lowpass_filter" in h2 else np.nan
        h2hpf = h2["highpass_filter"] if "highpass_filter" in h2 else np.nan
        filter_dict = {
            "H1Lowpass": h1lpf,
            "H1Highpass": h1hpf,
            "H2Lowpass": h2lpf,
            "H2Highpass": h2hpf,
        }

    dists = summary.distances
    row = {
        "EarthquakeId": event["id"] if "id" in event else event.id,
        "EarthquakeTime": event["time"] if "time" in event else event.time,
        "EarthquakeLatitude": (
            event["latitude"] if "latitude" in event else event.latitude
        ),
        "EarthquakeLongitude": (
            event["longitude"] if "longitude" in event else event.longitude
        ),
        "EarthquakeDepth": event["depth"] if "depth" in event else event.depth_km,
        "EarthquakeMagnitude": (
            event["magnitude"] if "magnitude" in event else event.magnitude
        ),
        "EarthquakeMagnitudeType": (
            event["magnitude_type"]
            if "magnitude_type" in event
            else event.magnitude_type
        ),
        "Network": tr["network"],
        "DataProvider": tr["source"],
        "StationCode": tr["station"],
        "StationID": station_id,
        "StationDescription": tr["station_name"],
        "StationLatitude": tr["latitude"],
        "StationLongitude": tr["longitude"],
        "StationElevation": tr["elevation"],
        "SamplingRate": tr["sampling_rate"],
        "BackAzimuth": summary._back_azimuth,
        "EpicentralDistance": dists["epicentral"],
        "HypocentralDistance": dists["hypocentral"],
        "SourceFile": tr["source_file"] if "source_file" in tr else "",
    }
    if "rupture" in dists:
        row.update({"RuptureDistance": dists["rupture"]})
        row.update({"RuptureDistanceVar": dists["rupture_var"]})
    if "joyner_boore" in dists:
        row.update({"JoynerBooreDistance": dists["joyner_boore"]})
        row.update({"JoynerBooreDistanceVar": dists["joyner_boore_var"]})
    if "gc2_rx" in dists:
        row.update({"GC2_rx": dists["gc2_rx"]})
    if "gc2_ry" in dists:
        row.update({"GC2_ry": dists["gc2_ry"]})
    if "gc2_ry0" in dists:
        row.update({"GC2_ry0": dists["gc2_ry0"]})
    if "gc2_U" in dists:
        row.update({"GC2_U": dists["gc2_U"]})
    if "gc2_T" in dists:
        row.update({"GC2_T": dists["gc2_T"]})

    # Add the filter frequency information to the row
    row.update(filter_dict)

    imt_frame = summary.pgms.xs(imc, level=1)
    row.update(imt_frame.Result.to_dict())
    return row
