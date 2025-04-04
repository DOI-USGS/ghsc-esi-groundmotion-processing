"""Module for COSMOS reader."""

# stdlib imports
import logging
import os
import pathlib
import re
from datetime import datetime

# third party
import numpy as np
import scipy.constants as sp
from gmprocess.core.stationstream import StationStream
from gmprocess.core.stationtrace import PROCESS_LEVELS, StationTrace

# local imports
from gmprocess.io.cosmos.data_structures import (
    BUILDING_TYPES,
    COSMOS_NETWORKS,
    COSMOS_ORIENTATIONS,
)
from gmprocess.io.seedname import get_channel_name
from gmprocess.io.utils import is_binary
from gmprocess.utils.constants import UNIT_CONVERSIONS
from obspy.core.trace import Stats

TIMEFMT = "%Y-%m-%dT%H:%M:%SZ"
MICRO_TO_VOLT = 1e6  # convert microvolts to volts
MSEC_TO_SEC = 1 / 1000.0
TEXT_HDR_ROWS = 14
VALID_MARKERS = [
    "CORRECTED ACCELERATION",
    "UNCORRECTED ACCELERATION",
    "RAW ACCELERATION COUNTS",
]

code_file = pathlib.Path(__file__).parent / ".." / ".." / "data" / "fdsn_codes.csv"

CODES, SOURCES1, SOURCES2 = np.genfromtxt(
    code_file,
    skip_header=1,
    usecols=(0, 1, 2),
    encoding="latin-1",
    unpack=True,
    dtype=bytes,
    delimiter=",",
)

# Updated tables:
# https://www.strongmotioncenter.org/NCESMD/reports/COSMOS_Tables.pdf

CODES = CODES.astype(str)


VALID_AZIMUTH_INTS = np.concatenate([np.arange(1, 361), list(COSMOS_ORIENTATIONS)])


FILTERS = {
    0: "None",
    1: "Rectangular",
    2: "Cosine bell",
    3: "Ormsby",
    4: "Butterworth single direction",
    5: "Butterworth bi-directional",
    6: "Bessel",
}

PHYSICAL_UNITS = {
    1: ("s", np.nan),
    2: ("g", 980.665),
    3: ("ss & g", np.nan),
    4: ("cm/s/s", 1.0),
    5: ("cm/s", 1.0),
    6: ("cm", 1.0),
    7: ("in/s/s", 2.54),
    8: ("in/s", 2.54),
    9: ("in", 2.54),
    10: ("gal", 1.0),
    11: ("mg", 0.980665),
    12: ("micro g", np.nan),
    23: ("deg/s/s", np.nan),
    24: ("deg/s", np.nan),
    25: ("deg", np.nan),
    50: ("counts", np.nan),
    51: ("volts", np.nan),
    22: ("mvolts", np.nan),
    60: ("psi", np.nan),
    80: ("micro strain", np.nan),
}

UNITS = {
    1: "acc",
    2: "vel",
    3: "disp",
    4: "Relative Displacement",
    10: "Angular Acceleration",
    11: "Angular Velocity",
    12: "Angular Displacement",
    20: "Absolute Pressure",
    21: "Relative Pressure (gage)",
    30: "Volumetric Strain",
    31: "Linear Strain",
}

SENSOR_TYPES = {
    1: "Optical-mechanical accelerometer",
    2: "Kinemetrics FBA-1 accelerometer",
    3: "Kinemetrics FBA-3 accelerometer",
    4: "Kinemetrics FBA-11 accelerometer",
    5: "Kinemetrics FBA-13 accelerometer",
    6: "Kinemetrics FBA-13DH accelerometer",
    7: "Kinemetrics FBA-23 accelerometer",
    8: "Kinemetrics FBA-23DH accelerometer",
    20: "Kinemetrics Episensor accelerometer",
    21: "Kinemetrics Episensor ES-U accelerometer",
    50: "Sprengnether FBX-23 accelerometer",
    51: "Sprengnether FBX-26 accelerometer",
    100: "Terratech SSA 120 accelerometer",
    101: "Terratech SSA 220 accelerometer",
    102: "Terratech SSA 320 accelerometer",
    150: "Wilcoxson 731A accelerometer",
    200: "Guralp CMG-5 accelerometer",
    900: "Other accelerometer",
    1001: "Kinemetrics SS-1 Ranger velocity sensor",
    1050: "Sprengnether S-3000 velocity sensor",
    1201: "Guralp CMG-1 velocity sensor",
    1202: "Guralp CMG-3T velocity sensor",
    1203: "Guralp CMG-3ESP velocity sensor",
    1204: "Guralp CMG-40 velocity sensor",
    1250: "Strecheisen STS-1 velocity sensor",
    1251: "Strecheisen STS-2 velocity sensor",
    1300: "Mark Products L4 velocity sensor",
    1301: "Mark Products L22D velocity sensor",
    1900: "Other velocity sensor",
    3000: "Other pressure series",
    3500: "Other Dilatometer series",
    4000: "Other Relative displacement series",
    4500: "Other Rotational series",
    9000: "Other Other series",
}


def is_cosmos(filename, config=None, v2=False):
    """Check to see if file is a COSMOS V0/V1 strong motion file.

    Args:
        filename (str):
            Path to possible COSMOS V0/V1 data file.
        config (dict):
            Dictionary containing configuration.
        v2 (bool):
            Include v2 velocity and displacement traces.

    Returns:
        bool: True if COSMOS V0/V1, False otherwise.
    """
    valid_markers = VALID_MARKERS.copy()
    if v2:
        valid_markers.extend(
            [
                "Velocity data",
                "Corrected velocity",
                "Displacement data",
                "Corrected displacement",
            ]
        )
    if is_binary(filename):
        return False
    try:
        line = open(filename, "rt", encoding="utf-8").readline()
        for marker in valid_markers:
            if line.lower().find(marker.lower()) >= 0:
                if line.lower().find("(format v") >= 0:
                    return True
    except UnicodeDecodeError:
        return False
    return False


def read_cosmos(filename, config=None, v2=False, use_original_chan=False, **kwargs):
    """Read COSMOS V1/V2 strong motion file.

    There is one extra key in the Stats object for each Trace -
    "process_level". This will be set to either "V1" or "V2".

    Args:
        filename (str):
            Path to possible COSMOS V1/V2 data file.
        config (dict):
            Dictionary containing configuration.
        v2 (bool):
            Include v2 velocity and displacement traces.
        use_original_chan (bool):
            Don't try to sort out consistent channel naming.
        kwargs (ref):
            valid_station_types (list):
                List of valid station types. See table 6 in the COSMOS strong motion
                data format documentation for station type codes.
            Other arguments will be ignored.

    Returns:
        list: List of StationStreams containing three channels of acceleration
        data (cm/s**2).
    """
    if not is_cosmos(filename, config, v2):
        raise Exception(f"{filename} is not a valid COSMOS strong motion data file.")
    # get list of valid stations
    valid_station_types = kwargs.get("valid_station_types", None)
    # get list of valid stations
    location = kwargs.get("location", "")

    # count the number of lines in the file
    with open(filename, encoding="utf-8") as f:
        line_count = sum(1 for _ in f)

    # read as many channels as are present in the file
    line_offset = 0
    stream = StationStream([], config=config)
    while line_offset < line_count:
        trace, line_offset = _read_channel(
            filename,
            line_offset,
            location=location,
            config=config,
            use_original_chan=use_original_chan,
        )
        # store the trace if the station type is in the valid_station_types
        # list or store the trace if there is no valid_station_types list
        if valid_station_types is not None:
            scode = trace.stats["format_specific"]["station_code"]
            if scode in valid_station_types:
                stream.append(trace)
        else:
            stream.append(trace)

    return [stream]


def _read_channel(
    filename, line_offset, location="", config=None, use_original_chan=False
):
    """Read channel data from COSMOS V1/V2 text file.

    Args:
        filename (str):
            Input COSMOS V1/V2 filename.
        line_offset (int):
            Line offset to beginning of channel text block.
        use_original_chan (book):
            Do not try to sort out consistent channel naming system.

    Returns:
        tuple: (obspy Trace, int line offset)
    """
    # read station, location, and process level from text header
    with open(filename, "rt", encoding="utf-8") as f:
        for _ in range(line_offset):
            next(f)
        lines = [next(f) for x in range(TEXT_HDR_ROWS)]

    # read in lines of integer data
    skiprows = line_offset + TEXT_HDR_ROWS
    int_lines, int_data = _read_lines(skiprows, filename)
    int_data = int_data.astype(np.int32)

    # read in lines of float data
    skiprows += int_lines + 1
    flt_lines, flt_data = _read_lines(skiprows, filename)

    # read in comment lines
    skiprows += flt_lines + 1
    cmt_lines, cmt_data = _read_lines(skiprows, filename)
    skiprows += cmt_lines + 1

    # according to the powers that defined the Network.Station.Channel.Location
    # "standard", Location is a two character field.  Most data providers,
    # including cosmos here, don't provide this.  We'll flag it as "--".
    hdr = _get_header_info(
        int_data,
        flt_data,
        lines,
        cmt_data,
        location=location,
        use_original_chan=use_original_chan,
    )
    head, tail = os.path.split(filename)
    hdr["standard"]["source_file"] = tail or os.path.basename(head)

    # read in the data
    nrows, data = _read_lines(skiprows, filename)

    # Check for "off-by-one" problem that sometimes occurs with cosmos data
    # Notes:
    #     - We cannot do this check inside _get_header_info because we don't
    #       have the data there.
    #     - That method is written to set npts from the header as documented in
    #       the spec ("lenght" == npts*dt) but it appears that sometimes a
    #       different convention is used where the "length" of the record is
    #       actually is actuation (npts-1)*dt. In this case, we need to
    #       recompute duration and npts
    if hdr["npts"] == (len(data) - 1):
        hdr["npts"] = len(data)
        hdr["duration"] = (hdr["npts"] - 1) * hdr["delta"]

    # check units
    if hdr["standard"]["units_type"] == "acc":
        unit = hdr["format_specific"]["physical_units"]
        hdr["standard"]["units"] = unit
        if unit in UNIT_CONVERSIONS:
            data *= UNIT_CONVERSIONS[unit]
        else:
            if unit != "counts":
                raise ValueError(f"COSMOS: {unit} is not a supported unit.")

    trace = StationTrace(data.copy(), Stats(hdr.copy()), config=config)

    # record that this data has been converted to g, if it has
    if (
        hdr["standard"]["process_level"] != PROCESS_LEVELS["V0"]
        and hdr["standard"]["units_type"] == "acc"
    ):  # We multiply by UNIT_CONVERSIONS above, so this is cm/s/s
        response = {"input_units": "counts", "output_units": "cm/s/s"}
    else:
        response = {
            "input_units": "counts",
            "output_units": hdr["format_specific"]["physical_units"],
        }
    trace.set_provenance("remove_response", response)

    # set new offset
    new_offset = skiprows + nrows
    new_offset += 1  # there is an 'end of record' line after the data

    return (trace, new_offset)


def _get_header_info(
    int_data, flt_data, lines, cmt_data, location="", use_original_chan=False
):
    """Return stats structure from various headers.

    Output is a dictionary like this:
     - network (str): Default is '--'. Determined using COSMOS_NETWORKS
     - station (str)
     - channel (str): Determined using COSMOS_ORIENTATIONS
     - location (str): Set to location index of sensor site at station.
            If not a multi-site array, default is '--'.
     - starttime (datetime)
     - duration (float)
     - sampling_rate (float)
     - delta (float)
     - npts (int)
     - coordinates:
       - latitude (float)
       - longitude (float)
       - elevation (float)
    - standard (Defaults are either np.nan or '')
      - horizontal_orientation (float): Rotation from north (degrees)
      - instrument_period (float): Period of sensor (Hz)
      - instrument_damping (float): Fraction of critical
      - process_time (datetime): Reported date of processing
      - process_level: Either 'V0', 'V1', 'V2', or 'V3'
      - station_name (str): Long form station description
      - sensor_serial_number (str): Reported sensor serial
      - instrument (str): See SENSOR_TYPES
      - comments (str): Processing comments
      - structure_type (str): See BUILDING_TYPES
      - corner_frequency (float): Sensor corner frequency (Hz)
      - units (str): See UNITS
      - source (str): Network source description
      - source_format (str): Always cosmos
    - format_specific
      - physical_units (str): See PHYSICAL_UNITS
      - v30 (float): Site geology V30 (km/s)
      - least_significant_bit: Recorder LSB in micro-volts (uv/count)
      - low_filter_type (str): Filter used for low frequency
            V2 filtering (see FILTERS)
      - low_filter_corner (float): Filter corner for low frequency
            V2 filtering (Hz)
      - low_filter_decay (float): Filter decay for low frequency
            V2 filtering (dB/octabe)
      - high_filter_type (str): Filter used for high frequency
            V2 filtering (see FILTERS)
      - high_filter_corner (float): Filter corner for high frequency
            V2 filtering (Hz)
      - high_filter_decay (float): Filter decay for high frequency
            V2 filtering (dB/octabe)
      - maximum (float): Maximum value
      - maximum_time (float): Time at which maximum occurs
      - station_code (int): Code for structure_type
      - record_flag (str): Either 'No problem', 'Fixed', 'Unfixed problem'.
            Should be described in more depth in comments.
      - scaling_factor (float): Scaling used for converting acceleration
            from g/10 to cm/s/s
      - sensor_sensitivity (float): Sensitvity in volts/g

    Args:
        int_data (ndarray):
            Array of integer data.
        flt_data (ndarray):
            Array of float data.
        lines (list):
            List of text headers (str).
        cmt_data (ndarray):
            Array of comments (str).
        location (str):
            Location metadata.
        use_original_chan (bool):
            Do not try to sort out channel based on orientation informaiton.

    Returns:
        dictionary: Dictionary of header/metadata information
    """
    hdr = {}
    coordinates = {}
    standard = {}
    format_specific = {}

    # Get unknown parameter number
    try:
        unknown_int = int(lines[12][64:71])
    except ValueError:
        unknown_int = -999
    try:
        unknown_flt = float(lines[12][72:80])
    except ValueError:
        unknown_flt = -999.0

    # Get network from cosmos table or fdsn code sheet
    if int_data[10] == unknown_int:
        network = "--"
        source = ""
    elif int_data[10] in COSMOS_NETWORKS:
        network = COSMOS_NETWORKS[int_data[10]][0]
        source = COSMOS_NETWORKS[int_data[10]][1]
        if network == "":
            network = COSMOS_NETWORKS[int_data[10]][2]
    else:
        network_code = lines[4][25:27].upper()
        if network_code in CODES:
            network = network_code
            idx = np.argwhere(CODES == network_code)[0][0]
            source = (
                SOURCES1[idx].decode("utf-8") + ", " + SOURCES2[idx].decode("utf-8")
            )
        else:
            network = "--"
            source = ""
    hdr["network"] = network
    hdr["station"] = lines[4][28:34].strip()

    # the channel orientation can be either relative to true north (idx 53)
    # or relative to sensor orientation (idx 54).
    if int_data[53] != unknown_int:
        horizontal_angle = int(int_data[53])
    else:
        horizontal_angle = np.nan

    if horizontal_angle not in VALID_AZIMUTH_INTS:
        angles_int = int_data[19:21]
        angles_float = angles_int.astype(np.float32)
        angles_float[angles_int == unknown_int] = np.nan
        if np.any(~np.isnan(angles_float)):
            ref = angles_float[~np.isnan(angles_float)][0]
            horizontal_angle = int(int_data[54])
            if horizontal_angle not in VALID_AZIMUTH_INTS:
                raise ValueError("Horizontal_angle in COSMOS header is not valid.")
            else:
                horizontal_angle += ref
                if horizontal_angle > 360:
                    horizontal_angle -= 360

    horizontal_angle = float(horizontal_angle)

    # Store delta and duration. Use them to calculate npts and sampling_rate

    # NOTE: flt_data[33] is the delta of the V0 format, and if we are reading
    # a V1 or V2 format then it may have been resampled. We should consider
    # adding flt_data[33] delta to the provenance record at some point.

    if flt_data[61] != unknown_flt:
        delta = float(flt_data[61]) * MSEC_TO_SEC
        hdr["delta"] = delta
        hdr["sampling_rate"] = 1 / delta
    else:
        hdr["delta"] = np.nan
        hdr["sampling_rate"] = np.nan

    # Determine the angle based upon the cosmos table
    # Set horizontal angles other than N,S,E,W to H1 and H2
    # Missing angle results in the channel number
    if not np.isnan(horizontal_angle):
        if horizontal_angle in COSMOS_ORIENTATIONS:
            channel = COSMOS_ORIENTATIONS[horizontal_angle][1].upper()
            if channel == "UP" or channel == "DOWN" or channel == "VERT":
                channel = get_channel_name(
                    hdr["sampling_rate"],
                    is_acceleration=True,
                    is_vertical=True,
                    is_north=False,
                )
                horizontal_angle = 360.0
            elif channel == "RADL" or channel == "LONG" or channel == "H1":
                channel = get_channel_name(
                    hdr["sampling_rate"],
                    is_acceleration=True,
                    is_vertical=False,
                    is_north=True,
                )
                horizontal_angle = 0.0
            elif channel == "TRAN" or channel == "TANG" or channel == "H2":
                channel = get_channel_name(
                    hdr["sampling_rate"],
                    is_acceleration=True,
                    is_vertical=False,
                    is_north=False,
                )
                horizontal_angle = 90.0
            else:  # For the occasional 'OTHR' channel
                raise ValueError("Channel name is not valid.")

        elif horizontal_angle >= 0 and horizontal_angle <= 360:
            if (
                horizontal_angle > 315
                or horizontal_angle < 45
                or (horizontal_angle > 135 and horizontal_angle < 225)
            ):
                channel = get_channel_name(
                    hdr["sampling_rate"],
                    is_acceleration=True,
                    is_vertical=False,
                    is_north=True,
                )
            else:
                channel = get_channel_name(
                    hdr["sampling_rate"],
                    is_acceleration=True,
                    is_vertical=False,
                    is_north=False,
                )
        horizontal_orientation = horizontal_angle
    else:
        errstr = (
            "Not enough information to distinguish horizontal from "
            "vertical channels."
        )
        raise ValueError("COSMOS: " + errstr)

    # Override channel name if necessary
    if use_original_chan:
        scnl_line = [line for line in cmt_data if line.startswith("|<SCNL>")]
        if scnl_line:
            channel = scnl_line[0].replace("|<SCNL>", "").split(".")[1]
        else:
            raise ValueError("No SCNL line found, cannot get original channel name.")

    hdr["channel"] = channel
    if location:
        hdr["location"] = location
    else:
        if int_data[55] != unknown_int:
            location = str(int(int_data[55]))
        else:
            location = "--"
        if len(location) < 2:
            location = location.zfill(2)
        hdr["location"] = location

    if int_data[39] != unknown_int:
        year = int_data[39]
    else:
        year = np.nan
    if int_data[41] != unknown_int:
        month = int_data[41]
    else:
        month = np.nan
    if int_data[42] != unknown_int:
        day = int_data[42]
    else:
        day = np.nan
    if int_data[43] != unknown_int:
        hour = int_data[43]
    else:
        hour = np.nan
    if int_data[44] != unknown_int:
        minute = int(int_data[44])
    else:
        minute = np.nan
    if flt_data[29] != unknown_flt:
        second = float(flt_data[29])
    else:
        second = np.nan

    # Inadequate time information if anything more than seconds is excluded
    if np.isnan(second):
        try:
            hdr["starttime"] = datetime(year, month, day, hour, minute)
        except BaseException:
            raise ValueError("COSMOS: Inadequate start time information.")
    else:
        microsecond = int((second - int(second)) * 1e6)
        try:
            hdr["starttime"] = datetime(
                year, month, day, hour, minute, int(second), microsecond
            )
        except BaseException:
            raise ValueError("COSMOS: Inadequate start time information.")

    if flt_data[62] != unknown_flt:
        # COSMOS **defines** "length" as npts*dt (note this is a bit unusual)
        cosmos_length = flt_data[62]
        npts = int(cosmos_length / delta)
        hdr["duration"] = (npts - 1) * delta
        hdr["npts"] = npts
    else:
        raise ValueError("COSMOS file does not specify length.")

    # coordinate information
    if flt_data[0] != unknown_flt:
        coordinates["latitude"] = float(flt_data[0])
    else:
        raise ValueError("Latitude is unknown.")
    if flt_data[1] != unknown_flt:
        coordinates["longitude"] = float(flt_data[1])
    else:
        raise ValueError("Longitude is unknown.")
    if flt_data[2] != unknown_flt:
        coordinates["elevation"] = float(flt_data[2])
    else:
        coordinates["elevation"] = 0.0
        logging.warning("Missing elevation. Setting to 0.0.")

    hdr["coordinates"] = coordinates

    # standard metadata
    standard["source"] = source
    standard["horizontal_orientation"] = horizontal_orientation
    standard["vertical_orientation"] = np.nan
    standard["station_name"] = lines[4][40:-1].strip()

    if flt_data[39] != unknown_flt:
        instrument_frequency = float(flt_data[39])
    else:
        instrument_frequency = np.nan
    standard["instrument_period"] = 1.0 / instrument_frequency
    if flt_data[40] != unknown_flt:
        standard["instrument_damping"] = float(flt_data[40])
    else:
        standard["instrument_damping"] = np.nan

    process_line = lines[10][10:40]
    if process_line.find("-") >= 0 or process_line.find("/") >= 0:
        if process_line.find("-") >= 0:
            delimeter = "-"
        elif process_line.find("/") >= 0:
            delimeter = "/"
        try:
            date = process_line.split(delimeter)
            month = int(date[0][-2:])
            day = int(date[1])
            year = int(date[2][:4])
            time = process_line.split(":")
            hour = int(time[0][-2:])
            minute = int(time[1])
            second = float(time[2][:2])
            microsecond = int((second - int(second)) * 1e6)
            etime = datetime(year, month, day, hour, minute, int(second), microsecond)
            standard["process_time"] = etime.strftime(TIMEFMT)
        except BaseException:
            standard["process_time"] = ""
    else:
        standard["process_time"] = ""

    if int_data[0] != unknown_int:
        process_level = int(int_data[0])
    else:
        raise ValueError("Unknown process level.")
    if process_level == 0:
        standard["process_level"] = PROCESS_LEVELS["V0"]
    elif process_level == 1:
        standard["process_level"] = PROCESS_LEVELS["V1"]
    elif process_level == 2:
        standard["process_level"] = PROCESS_LEVELS["V2"]
    elif process_level == 3:
        standard["process_level"] = PROCESS_LEVELS["V3"]
    else:
        standard["process_level"] = PROCESS_LEVELS["V1"]

    if int_data[52] != unknown_int:
        standard["sensor_serial_number"] = str(int_data[52])
    else:
        standard["sensor_serial_number"] = ""

    if int_data[51] != unknown_int:
        instrument = int(int_data[51])
        if instrument in SENSOR_TYPES:
            standard["instrument"] = SENSOR_TYPES[instrument]
        else:
            standard["instrument"] = lines[6][57:-1].strip()
    else:
        standard["instrument"] = lines[6][57:-1].strip()

    if int_data[18] != unknown_int:
        structure_type_code = int(int_data[18])
    else:
        structure_type_code = np.nan
    if structure_type_code in BUILDING_TYPES:
        standard["structure_type"] = BUILDING_TYPES[structure_type_code]
    else:
        standard["structure_type"] = ""

    if flt_data[25] != unknown_flt:
        standard["corner_frequency"] = flt_data[25]
    else:
        standard["corner_frequency"] = np.nan

    if int_data[2] != unknown_int:
        physical_parameter = int_data[2]
    else:
        physical_parameter = np.nan

    if int_data[1] != unknown_int:
        unit_code = int_data[1]
    else:
        unit_code = np.nan

    if unit_code in UNITS:
        standard["units_type"] = UNITS[unit_code]
    else:
        if physical_parameter in [2, 4, 7, 10, 11, 12, 23]:
            standard["units_type"] = "acc"
        elif physical_parameter in [5, 8, 24]:
            standard["units_type"] = "vel"
        elif physical_parameter in [6, 9, 25]:
            standard["units_type"] = "disp"

    standard["source_format"] = "cosmos"

    standard["comments"] = ", ".join(cmt_data)

    # get undocumented SCNL code if it is present because location code doesn't seem to
    # be reported in the header.
    if "<SCNL>" in standard["comments"]:
        scnl = re.search(r"<SCNL>(.*?)(?=\s)", standard["comments"]).group(1)  # noqa
        # Do not use channel from here because we got it from orientation info
        # previously
        hdr["station"], _, hdr["network"], hdr["location"] = scnl.split(".")

    # format specific metadata
    if physical_parameter in PHYSICAL_UNITS:
        physical_parameter = PHYSICAL_UNITS[physical_parameter][0]
    format_specific["physical_units"] = physical_parameter

    if flt_data[3] != unknown_flt:
        format_specific["v30"] = float(flt_data[3])
    else:
        format_specific["v30"] = np.nan

    if flt_data[21] != unknown_flt:
        format_specific["least_significant_bit"] = float(flt_data[21])
    else:
        format_specific["least_significant_bit"] = np.nan

    if flt_data[46] != unknown_flt:
        format_specific["gain"] = float(flt_data[46])
    else:
        format_specific["gain"] = np.nan

    if int_data[60] != unknown_int:
        low_filter_type = int(int_data[60])
        if low_filter_type in FILTERS:
            format_specific["low_filter_type"] = FILTERS[low_filter_type]
        else:
            format_specific["low_filter_type"] = ""
    else:
        format_specific["low_filter_type"] = ""

    if flt_data[53] != unknown_flt:
        format_specific["low_filter_corner"] = float(flt_data[53])
    else:
        format_specific["low_filter_corner"] = np.nan

    if flt_data[54] != unknown_flt:
        format_specific["low_filter_decay"] = float(flt_data[54])
    else:
        format_specific["low_filter_decay"] = np.nan

    if int_data[61] != unknown_int:
        high_filter_type = int(int_data[61])
        if high_filter_type in FILTERS:
            format_specific["high_filter_type"] = FILTERS[high_filter_type]
        else:
            format_specific["high_filter_type"] = ""
    else:
        format_specific["high_filter_type"] = ""

    if flt_data[56] != unknown_flt:
        format_specific["high_filter_corner"] = float(flt_data[56])
    else:
        format_specific["high_filter_corner"] = np.nan

    if flt_data[57] != unknown_flt:
        format_specific["high_filter_decay"] = float(flt_data[57])
    else:
        format_specific["high_filter_decay"] = np.nan

    if flt_data[63] != unknown_flt:
        format_specific["maximum"] = float(flt_data[63])
    else:
        format_specific["maximum"] = np.nan

    if flt_data[64] != unknown_flt:
        format_specific["maximum_time"] = float(flt_data[64])
    else:
        format_specific["maximum_time"] = np.nan

    format_specific["station_code"] = structure_type_code

    record_flag = int(int_data[75])
    if record_flag == 0:
        format_specific["record_flag"] = "No problem"
    elif record_flag == 1:
        format_specific["record_flag"] = "Fixed"
    elif record_flag == 2:
        format_specific["record_flag"] = "Unfixed problem"
    else:
        format_specific["record_flag"] = ""

    if flt_data[87] != unknown_flt:
        format_specific["scaling_factor"] = float(flt_data[87])
    else:
        format_specific["scaling_factor"] = np.nan

    if flt_data[21] != unknown_flt:
        format_specific["data_logger_sensitivity"] = float(flt_data[21])
    else:
        format_specific["data_logger_sensitivity"] = np.nan

    if flt_data[41] != unknown_flt:
        format_specific["stage_1_sensitivity"] = float(flt_data[41])
    else:
        format_specific["stage_1_sensitivity"] = np.nan

    # for V0 files, set a standard field called instrument_sensitivity
    # least_significant_bit is real header 22 in COSMOS docs.
    # units are microvolts/count
    ctov = format_specific["least_significant_bit"] / MICRO_TO_VOLT
    # stage_1_sensitivity is real header 43, i.e., "sensor sensitivity" in COSMOS docs
    # with units of volts/g
    vtog = 1 / format_specific["stage_1_sensitivity"]
    if not np.isnan(format_specific["gain"]):
        gain = format_specific["gain"]
    else:
        gain = 1.0
    if gain == 0:
        fmt = "%s.%s.%s.%s"
        tpl = (hdr["network"], hdr["station"], hdr["channel"], hdr["location"])
        nscl = fmt % tpl
        raise ValueError(f"Gain of 0 discovered for NSCL: {nscl}")
    denom = ctov * vtog * (1.0 / gain) * sp.g
    standard["instrument_sensitivity"] = 1 / denom
    standard["volts_to_counts"] = ctov

    # Set dictionary
    hdr["standard"] = standard
    hdr["coordinates"] = coordinates
    hdr["format_specific"] = format_specific
    return hdr


def _read_lines(skip_rows, filename):
    """Read lines of comments and data exluding headers.

    Args:
        skip_rows (int):
            Number of rows to skip.
        filename (str):
            Path to possible COSMOS V0/V1 data file.
    Returns:
        array-like: List of comments or array of data.
    """
    # read the headers
    header = np.genfromtxt(filename, skip_header=skip_rows - 1, max_rows=1, dtype="str")

    # parse the number of points and convert the header to a string
    npts = int(header[0])
    header = np.array_str(header).lower().replace("'", "").replace(" ", "").lower()

    # determine whether the following lines are comments or data
    if header.lower().find("comment") >= 0:
        num_lines = npts

        # read and store comment lines
        with open(filename, "rt", encoding="utf-8") as f:
            file = f.readlines()
        max_lines = skip_rows + num_lines
        comment = [file[idx] for idx in range(skip_rows, max_lines)]
        data_arr = comment
    else:
        # parse out the format of the data
        # sometimes header has newline characters in it...
        header = header.replace("\n", "")
        format_data = re.findall(r"\d+", header[header.find("format=") + 8 :])
        cols = int(format_data[0])
        fmt = int(format_data[1])
        num_lines = int(np.ceil(npts / cols))
        widths = [fmt] * cols

        # read data
        data_arr = np.genfromtxt(
            filename,
            skip_header=skip_rows,
            max_rows=num_lines,
            dtype=np.float64,
            delimiter=widths,
        ).flatten()
        # Strip off nans that are created by genfromtxt when the last
        # row is incomplete
        data_arr = data_arr[~np.isnan(data_arr)]
    return num_lines, data_arr


def write_cosmos(filename, label):
    pass
