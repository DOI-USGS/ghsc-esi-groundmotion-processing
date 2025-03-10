"""Module for ESM reader."""

# stdlib imports
import logging
import os
from datetime import datetime

import numpy as np
from gmprocess.core.stationstream import StationStream

# local imports
from gmprocess.core.stationtrace import PROCESS_LEVELS, StationTrace
from gmprocess.io.utils import is_binary

# third party
from obspy.core.trace import Stats

TEXT_HDR_ROWS = 64

TIMEFMTS = (
    "%Y%m%d_%H%M%S",  # 20190728_160919
    "%Y%m%d_%H%M%S.%f",  # 20190728_160919.870000
    "%Y-%m-%dT%H:%M:%S.%f",  # 2019-07-28T16:09:19.870000
    "%Y/%m/%d %H:%M:%S.%f",  # 2019/07/28 16:09:19.870000
    "%d/%m/%Y %H:%M:%S.%f",  # 28/07/2019 16:09:19.870000
)


SRC = "ORFEUS Engineering Strong Motion Database"
FORMAT = "ESM"

HDR1 = "EVENT_NAME:"
HDR2 = "EVENT_ID:"


def is_esm(filename, config=None):
    """Check to see if file is an ESM strong motion file.

    Args:
        filename (str):
            Path to possible ESM strong motion file.
        config (dict):
            Dictionary containing configuration.

    Returns:
        bool: True if ESM, False otherwise.
    """
    if is_binary(filename):
        return False

    if not os.path.isfile(filename):
        return False
    try:
        open(filename, "rt").read(os.stat(filename).st_size)
    except UnicodeDecodeError:
        return False
    try:
        with open(filename, "rt") as f:
            lines = [next(f) for x in range(TEXT_HDR_ROWS)]
            if lines[0].startswith(HDR1) and lines[1].startswith(HDR2):
                return True
    except BaseException:
        return False
    return False


def read_esm(filename, config=None, **kwargs):
    """Read European ESM strong motion file.

    Args:
        filename (str):
            Path to possible ESM data file.
        config (dict):
            Dictionary containing configuration.
        kwargs (ref):
            Other arguments will be ignored.

    Returns:
        Stream: Obspy Stream containing one channels of acceleration data
            (cm/s**2).
    """
    if not is_esm(filename, config):
        raise Exception(f"{filename} is not a valid ESM file")

    # Parse the header portion of the file
    header = {}
    with open(filename, "rt") as f:
        lines = [next(f) for x in range(TEXT_HDR_ROWS)]

    for line in lines:
        parts = line.split(":")
        key = parts[0].strip()
        value = ":".join(parts[1:]).strip()
        header[key] = value

    stats = {}
    standard = {}
    coordinates = {}
    # fill in all known stats header fields
    stats["network"] = header["NETWORK"]
    stats["station"] = header["STATION_CODE"]
    stats["channel"] = header["STREAM"]
    stats["location"] = "--"
    stats["delta"] = float(header["SAMPLING_INTERVAL_S"])
    stats["sampling_rate"] = 1 / stats["delta"]
    stats["calib"] = 1.0
    stats["npts"] = int(header["NDATA"])
    stimestr = header["DATE_TIME_FIRST_SAMPLE_YYYYMMDD_HHMMSS"]
    starttime = None
    for timefmt in TIMEFMTS:
        try:
            slen = min(len(stimestr), 26)  # maximum length of formatted string is 26
            starttime = datetime.strptime(stimestr[:slen], timefmt)
            break
        except Exception:
            continue
    if starttime:
        stats["starttime"] = starttime
    else:
        raise ValueError(f"Could not parse timestamp of first sample {stimestr}.")

    # fill in standard fields
    head, tail = os.path.split(filename)
    standard["source_file"] = tail or os.path.basename(head)
    standard["source"] = SRC
    standard["source_format"] = FORMAT
    standard["horizontal_orientation"] = np.nan
    standard["vertical_orientation"] = np.nan
    standard["station_name"] = header["STATION_NAME"]
    try:
        standard["instrument_period"] = 1 / float(header["INSTRUMENTAL_FREQUENCY_HZ"])
    except ValueError:
        standard["instrument_period"] = np.nan
    try:
        standard["instrument_damping"] = 1 / float(header["INSTRUMENTAL_DAMPING"])
    except ValueError:
        standard["instrument_damping"] = np.nan

    ptimestr = header["DATA_TIMESTAMP_YYYYMMDD_HHMMSS"]
    ptime = ""
    for timefmt in TIMEFMTS:
        try:
            slen = min(len(ptimestr), 26)  # maximum length of formatted string is 26
            ptime = datetime.strptime(ptimestr[:slen], timefmt)
            break
        except Exception:
            continue
    standard["process_time"] = str(ptime)
    standard["process_level"] = PROCESS_LEVELS["V1"]
    instr_str = header["INSTRUMENT"]
    parts = instr_str.split("|")
    sensor_str = parts[0].split("=")[1].strip()
    standard["sensor_serial_number"] = ""
    standard["instrument"] = sensor_str
    standard["comments"] = ""
    standard["structure_type"] = ""
    standard["units"] = "cm/s^2"
    standard["units_type"] = "acc"
    standard["instrument_sensitivity"] = np.nan
    standard["volts_to_counts"] = np.nan
    standard["corner_frequency"] = np.nan

    coordinates["latitude"] = float(header["STATION_LATITUDE_DEGREE"])
    coordinates["longitude"] = float(header["STATION_LONGITUDE_DEGREE"])
    coordinates["elevation"] = float(header["STATION_ELEVATION_M"])

    # read in the data
    data = np.genfromtxt(filename, skip_header=TEXT_HDR_ROWS)

    # create a Trace from the data and metadata
    stats["standard"] = standard
    stats["coordinates"] = coordinates
    trace = StationTrace(data.copy(), Stats(stats.copy()))
    response = {"input_units": "counts", "output_units": "cm/s^2"}
    trace.set_provenance("remove_response", response)
    ftype = header["FILTER_TYPE"].capitalize()
    try:
        forder = int(header["FILTER_ORDER"])
    except ValueError:
        forder = 0

    try:
        lowfreq = float(header["LOW_CUT_FREQUENCY_HZ"])
    except ValueError:
        lowfreq = np.nan
    try:
        highfreq = float(header["LOW_CUT_FREQUENCY_HZ"])
    except ValueError:
        highfreq = np.nan
    if not np.isnan(lowfreq) and not np.isnan(lowfreq):
        filter_att = {
            "filter_type": ftype,
            "lower_corner_frequency": lowfreq,
            "higher_corner_frequency": highfreq,
            "filter_order": forder,
        }

        trace.set_provenance("bandpass_filter", filter_att)
    detrend_att = {"detrending_method": "baseline"}
    if "NOT REMOVED" not in header["BASELINE_CORRECTION"]:
        trace.set_provenance("detrend", detrend_att)
    stream = StationStream(traces=[trace], config=config)
    return [stream]
