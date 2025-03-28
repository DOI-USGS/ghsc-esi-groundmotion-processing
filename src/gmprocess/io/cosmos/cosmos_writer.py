# stdlib imports
import io
import logging
import pathlib
import re
from collections import OrderedDict
import datetime
from enum import Enum

# third party imports
import numpy as np
import pandas as pd

# local imports
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.waveform_processing.integrate import get_disp, get_vel
from gmprocess.metrics.waveform_metric_collection import WaveformMetricCollection
from gmprocess.io.cosmos.core import BUILDING_TYPES, SENSOR_TYPES
from gmprocess.utils.constants import UNIT_TYPES, M_TO_CM
from obspy.core.utcdatetime import UTCDateTime
from obspy.geodetics.base import gps2dist_azimuth
from gmprocess.metrics.utils import component_to_channel

COSMOS_FORMAT = 1.2
UTC_TIME_FMT = "%m/%d/%Y, %H:%M:%S.%f"
AGENCY_RESERVED = "ASDF Converted"
EVENT_TIME_FMT = "%a %b %d, %Y %H:%M"
TIMEFMT = "%Y-%m-%dT%H:%M:%SZ"


class Volume(Enum):
    RAW = 0
    CONVERTED = 1
    PROCESSED = 2
    SPECTRA = 3


HEADER_LINES = 13
NUM_INT_VALUES = 100
INT_FMT = "%8d"
NUM_INT_ROWS = 10
NUM_INT_COLS = 10

NUM_FLOAT_VALUES = 100
FLOAT_FMT = "%15.6f"
NUM_FLOAT_ROWS = 20
NUM_FLOAT_COLS = 5

NUM_DATA_COLS = 1
FLOAT_DATA_FMT = "%15.6E"
SPECTRA_DATA_FMT = "%15.6E"
INT_DATA_FMT = "%8d"

TABLE1 = {"acc": 1, "vel": 2, "disp": 3}
TABLE2 = {"acc": 4, "vel": 5, "disp": 6, "counts": 50}
TABLE7 = {
    "US": 2,
    "BK": 3,
    "CI": 4,
    "NC": 5,
    "AZ": 7,
    "NN": 8,
    "C_": 9,
    " -": 10,
    "CE": 11,
    "TW": 100,
    "JP": 110,
    "BO": 111,
    "": 200,
}
SEISMIC_TRIGGER = 1
MISSING_DATA_INT = -999
MISSING_DATA_FLOAT = -999

REV_BUILDING_TYPES = {v: k for k, v in BUILDING_TYPES.items()}
REV_SENSOR_TYPES = {v: k for k, v in SENSOR_TYPES.items()}
CAUSAL_BUTTERWORTH_FILTER = 4
NONCAUSAL_BUTTERWORTH_FILTER = 5
FREQ_DOMAIN_FILTER = 1
NOMINAL_CONSTANTS_FLAG = 1
RECORD_PROBLEM_INDICATOR = 0
TIME_QUALITY_INDICATOR = 5
SOLID_STATE_RECORDING_MEDIUM = 3
GMT_OFFSET_HOURS = 0.0
TIME_CORRECTION = 0.0


def cfmt_to_ffmt(cfmt, ncols):
    ffmt = cfmt.replace("%", "")
    if "d" in cfmt:
        ffmt = str(ncols) + "I" + re.sub("d", "", ffmt, flags=re.IGNORECASE)
    elif "f" in cfmt:
        ffmt = str(ncols) + "F" + re.sub("f", "", ffmt, flags=re.IGNORECASE)
    else:
        ffmt = str(ncols) + "E" + re.sub("e", "", ffmt, flags=re.IGNORECASE)
    return ffmt


TEXT_HEADER_LINES = [
    ("param_type", "cosmos_format", "number_lines", "agency_reserved"),
    ("event_name", "event_local_time"),
    (
        "event_latitude",
        "event_longitude",
        "event_depth",
        "event_source",
        "event_magnitude",
    ),
    ("event_time", "source_agency"),
    (
        "network_number",
        "station_number",
        "network_code",
        "station_code",
        "network_abbrev",
        "station_name",
    ),
    ("station_latitude", "station_longitude", "site_geology"),
    (
        "recorder_type",
        "recorder_serial",
        "recorder_channels",
        "station_channels",
        "sensor_type",
        "sensor_serial",
    ),
    ("record_start", "time_quality", "record_id"),
    (
        "channel_number",
        "channel_azimuth",
        "recorder_channel_number",
        "sensor_location",
    ),
    ("record_duration", "raw_maximum", "raw_maximum_units", "raw_maximum_time"),
    (
        "processing_date",
        "data_maximum",
        "data_maximum_units",
        "data_maximum_time",
    ),
    ("low_band_hz", "low_band_sec", "high_band_hz"),
    ("missing_data_str", "missing_data_int", "missing_data_float"),
]


class Table4(object):
    def __init__(self, excelfile):
        self._dataframe = pd.read_excel(excelfile, na_filter=False)

    def get_cosmos_code(self, iris_code):
        row = self.get_row(iris_code)
        cosmos_code = row["Cosmos Code"]
        return cosmos_code

    def get_agency_desc(self, iris_code):
        row = self.get_row(iris_code)
        agency = row["Agency"]
        return agency

    def get_agency_abbrev(self, iris_code):
        row = self.get_row(iris_code)
        abbrev = row["Abbrev"]
        return abbrev

    def get_matching_network(self, eventid):
        eventid = eventid.lower()
        for _, row in self._dataframe.iterrows():
            network = row["IRIS Code"].lower()
            if eventid.startswith(network):
                return network
        return "--"

    def get_row(self, iris_code):
        iris_code = iris_code.upper()
        rows = self._dataframe.loc[self._dataframe["IRIS Code"] == iris_code]
        if not len(rows):
            iris_code = "--"
        rows = self._dataframe.loc[self._dataframe["IRIS Code"] == iris_code]
        return rows.iloc[0]


class TextHeader(object):
    # header_fmt tuples are (format_string, column offset, and value
    # (filled in by constructor))
    header_fmt = OrderedDict()
    # header_fmt["param_type"] = ["{value:25s}", 0, None]

    # line 1
    header_fmt["param_type"] = ["{value:25s}", 0, None]
    header_fmt["cosmos_format"] = ["(Format v{value:05.2f} ", 26, None]
    header_fmt["number_lines"] = ["with {value:2d} text lines)", 41, None]
    header_fmt["agency_reserved"] = ["{value:14s}", 61, None]

    # line 2
    header_fmt["event_name"] = ["{value:25s}", 0, None]
    header_fmt["event_local_time"] = ["{value:40s}", 26, None]

    # line 3
    header_fmt["event_latitude"] = ["Hypocenter:{value:7.3f}", 0, None]
    header_fmt["event_longitude"] = ["{value:8.3f}", 21, None]
    header_fmt["event_depth"] = ["H={value:3d}km", 32, None]
    header_fmt["event_source"] = ["({value:4s})", 39, None]
    header_fmt["event_magnitude"] = ["M={value:3.1f}", 46, None]

    # line 4
    header_fmt["event_time"] = ["Origin: {value:26s}", 0, None]
    header_fmt["source_agency"] = ["({value:4s})", 35, None]

    # line 5
    header_fmt["network_number"] = ["Statn No: {value:02d}-", 0, None]
    header_fmt["station_number"] = ["{value:5d}", 13, None]
    header_fmt["network_code"] = ["Code:{value:2s}-", 20, None]
    header_fmt["station_code"] = ["{value:6s}", 28, None]
    header_fmt["network_abbrev"] = ["{value:4s}", 35, None]
    header_fmt["station_name"] = ["{value:40s}", 40, None]

    # line 6
    header_fmt["station_latitude"] = ["Coords:{value:-8.4f}", 0, None]
    header_fmt["station_longitude"] = ["{value:-9.4f}", 16, None]
    header_fmt["site_geology"] = ["Site geology:{value:40s}", 27, None]

    # line 7
    header_fmt["recorder_type"] = ["Recorder: {value:6s}", 0, None]
    header_fmt["recorder_serial"] = ["s/n:{value:5s}", 17, None]
    header_fmt["recorder_channels"] = ["({value:3d}", 26, None]
    header_fmt["station_channels"] = [" Chns of {value:2d} at Sta)", 26, None]
    header_fmt["sensor_type"] = ["Sensor:{value:8s}", 50, None]
    header_fmt["sensor_serial"] = ["s/n {value:11s}", 68, None]

    # line 8
    header_fmt["record_start"] = ["Rcrd start time:{value:28s}", 0, None]
    header_fmt["time_quality"] = ["(Q={value:1s})", 45, None]
    header_fmt["record_id"] = ["RcrdId:{value:20s}", 51, None]

    # line 9
    header_fmt["channel_number"] = ["Sta Chan{value:4d}:", 0, None]
    header_fmt["channel_azimuth"] = ["{value:-3d} deg ", 13, None]
    header_fmt["recorder_channel_number"] = ["(Rcrdr Chan{value:3d}) ", 21, None]
    header_fmt["sensor_location"] = ["Location:{value:33s}", 37, None]

    # line 10
    header_fmt["record_duration"] = ["Raw record length ={value:8.3f} sec, ", 0, None]
    header_fmt["raw_maximum"] = ["Uncor max ={value:9.3f} ", 33, None]
    header_fmt["raw_maximum_units"] = ["{value:<6s} ", 53, None]
    header_fmt["raw_maximum_time"] = ["at {value:8.3f} sec", 59, None]

    # line 11
    header_fmt["processing_date"] = ["Processed:{value:28s}", 0, None]
    header_fmt["processing_agency"] = ["{value:5s}", 35, None]
    header_fmt["data_maximum"] = ["Max = {value:9.3f}", 41, None]
    header_fmt["data_maximum_units"] = ["{value:9s}", 57, None]
    header_fmt["data_maximum_time"] = ["at {value:7.3f} sec", 66, None]

    # line 12
    header_fmt["low_band_hz"] = ["Record filtered below{value:6.2f} Hz", 0, None]
    header_fmt["low_band_sec"] = ["(periods over{value:6.1f} secs)", 31, None]
    header_fmt["high_band_hz"] = ["and above{value:5.1f} Hz", 58, None]

    # line 13
    header_fmt["missing_data_str"] = ["{value:64s}", 0, None]
    header_fmt["missing_data_int"] = ["{value:7d},", 64, None]
    header_fmt["missing_data_float"] = ["{value:5.1f}", 73, None]

    def __init__(self, trace, scalar_event, stream, volume, config):
        datadir = pathlib.Path(__file__).parent / ".." / ".." / "data"
        excelfile = pathlib.Path(datadir) / "cosmos_table4.xls"
        table4 = Table4(excelfile)
        # fill in data for text header
        quantity = "velocity"
        if trace.stats.standard.units_type == "acc":
            quantity = "acceleration"
        level = "Raw"
        units = "counts"
        dmax = np.abs(trace.max())
        maxidx = np.where(np.abs(trace.data) == dmax)[0][0]
        if volume == Volume.CONVERTED:
            level = "Uncorrected"
            units = UNIT_TYPES[trace.stats.standard.units_type]
        elif volume == Volume.PROCESSED:
            level = "Corrected"
            units = UNIT_TYPES[trace.stats.standard.units_type]
        elif volume == Volume.SPECTRA:
            level = ""
            quantity = "Response spectra"
        maxtime = trace.stats.delta * maxidx  # seconds since rec start

        # line 1
        if volume == volume.RAW:
            self.set_header_value("param_type", f"{level} {quantity} {units}")
        else:
            self.set_header_value("param_type", f"{level} {quantity}")
        self.set_header_value("cosmos_format", COSMOS_FORMAT)
        self.set_header_value("number_lines", HEADER_LINES)
        self.set_header_value("agency_reserved", AGENCY_RESERVED)

        # line 2
        ename_str = f"Record of {scalar_event.id}"
        self.set_header_value("event_name", ename_str)
        # Leaving local time blank, because it is hard to determine correctly
        timestr = scalar_event.time.strftime(EVENT_TIME_FMT)
        self.set_header_value("event_local_time", f"Earthquake of {timestr} UTC")

        # line 3
        self.set_header_value("event_latitude", scalar_event.latitude)
        self.set_header_value("event_longitude", scalar_event.longitude)
        self.set_header_value("event_depth", int(np.round(scalar_event.depth_km)))
        iris_network = table4.get_matching_network(
            scalar_event.id.replace("smi:local/", "")
        )
        abbrev = table4.get_agency_abbrev(iris_network)
        self.set_header_value("event_source", abbrev)
        self.set_header_value("event_magnitude", scalar_event.magnitude)

        # line 4
        etime = scalar_event.time.strftime(UTC_TIME_FMT)[:-5] + " UTC"
        self.set_header_value("event_time", etime)
        self.set_header_value("source_agency", abbrev)

        # line 5
        netnum = table4.get_cosmos_code(trace.stats.network)
        self.set_header_value("network_number", netnum)
        self.set_header_value("station_number", 0)
        self.set_header_value("network_code", trace.stats.network)
        self.set_header_value("station_code", trace.stats.station)
        self.set_header_value(
            "network_abbrev", table4.get_agency_abbrev(trace.stats.network)
        )
        self.set_header_value("station_name", trace.stats.standard.station_name)

        # line 6
        self.set_header_value("station_latitude", trace.stats.coordinates.latitude)
        self.set_header_value("station_longitude", trace.stats.coordinates.longitude)
        self.set_header_value("site_geology", "Unknown")

        # line 7
        self.set_header_value("recorder_type", "")
        self.set_header_value("recorder_serial", "")
        self.set_header_value("recorder_channels", len(stream))
        self.set_header_value("station_channels", len(stream))
        instrument = trace.stats.standard.instrument.replace("None", "").strip()
        self.set_header_value("sensor_type", instrument)
        self.set_header_value(
            "sensor_serial", trace.stats.standard.sensor_serial_number
        )

        # line 8
        stime = trace.stats.starttime.strftime(UTC_TIME_FMT)[:-3] + " UTC"
        self.set_header_value("record_start", stime)
        # we don't know time quality, set to blank value
        self.set_header_value("time_quality", "")
        self.set_header_value("record_id", "(see comment)")

        # line 9
        channels = [trace.stats.channel for trace in stream]
        channel_number = channels.index(trace.stats.channel) + 1
        self.set_header_value("channel_number", channel_number)
        azimuth = trace.stats.standard.horizontal_orientation
        if trace.stats.standard.horizontal_orientation == 0:
            azimuth = 360.0
        self.set_header_value("channel_azimuth", int(azimuth))
        self.set_header_value("recorder_channel_number", channel_number)
        self.set_header_value("sensor_location", trace.stats.location)

        # line 10
        dtime = len(trace.data) * trace.stats.delta
        # dtime = trace.stats.endtime - trace.stats.starttime  # duration secs
        self.set_header_value("record_duration", dtime)
        if volume == Volume.RAW:
            self.set_header_value("raw_maximum", dmax)
            self.set_header_value("raw_maximum_units", units)
            self.set_header_value("raw_maximum_time", maxtime)
        else:
            self.set_header_value("raw_maximum", 0)
            self.set_header_value("raw_maximum_units", "")
            self.set_header_value("raw_maximum_time", 0)

        # line 11
        ptimestr = trace.stats.standard.process_time
        pdate = ""
        if len(ptimestr.strip()):
            ptime = datetime.datetime.strptime(ptimestr, TIMEFMT)
            pdate = ptime.strftime(UTC_TIME_FMT) + " UTC"
        self.set_header_value("processing_date", pdate)

        agency = "UNK"
        if "agency" in config:
            agency = config["agency"]
        self.set_header_value("processing_agency", agency)
        self.set_header_value("data_maximum", dmax)
        self.set_header_value("data_maximum_units", units)
        self.set_header_value("data_maximum_time", maxtime)

        # line 12
        if volume != volume.RAW:
            # self.set_header_value("high_band_hz", np.nan)
            # self.set_header_value("low_band_hz", np.nan)
            # self.set_header_value("low_band_sec", np.nan)
            msg = """The COSMOS format defines the corner frequencies to be computed
            based on a 3 DB cutoff frequency. gmprocess does not enforce this requirement."""
            logging.warning(msg)
            self.set_header_value(
                "high_band_hz",
                trace.get_parameter("corner_frequencies")["lowpass"],
            )
            self.set_header_value(
                "low_band_hz",
                trace.get_parameter("corner_frequencies")["highpass"],
            )
            self.set_header_value(
                "low_band_sec",
                1 / trace.get_parameter("corner_frequencies")["highpass"],
            )
        else:
            self.header_fmt["low_band_hz"] = [
                "Record filtered below{value:1} Hz",
                0,
                None,
            ]
            self.header_fmt["low_band_sec"] = [
                "(periods over{value:1} secs)",
                31,
                None,
            ]
            self.header_fmt["high_band_hz"] = ["and above{value:1} Hz", 58, None]
            self.set_header_value("high_band_hz", " ")
            self.set_header_value("low_band_hz", " ")
            self.set_header_value("low_band_sec", " ")

        # line 13
        miss_str = "Values used when parameter or data value is unknown/unspecified:"
        self.set_header_value("missing_data_str", miss_str)
        self.set_header_value("missing_data_int", MISSING_DATA_INT)
        self.set_header_value("missing_data_float", MISSING_DATA_FLOAT)

    def set_header_value(self, key, value):
        width = int(re.search(r"\d+", self.header_fmt[key][0]).group(0))
        if isinstance(value, str) and len(value) > width:
            value = value[0:width]
        formatted_value = self.header_fmt[key][0].format(value=value)
        self.header_fmt[key][2] = formatted_value

    def write(self, cosmos_file):
        # write out data for text header to cosmos_file object
        for line_keys in TEXT_HEADER_LINES:
            line = ""
            for line_key in line_keys:
                _, column_offset, value = self.header_fmt[line_key]
                offset = column_offset - len(line)
                if value is not None:
                    line += " " * offset + value
                else:
                    value = ""
                    line += " " * offset + value
            line = line.rstrip()
            cosmos_file.write(line + "\n")
        return None


class IntHeader(object):
    def __init__(self, trace, scalar_event, stream, volume, gmprocess_version):
        self.volume = volume
        self.scalar_event = scalar_event
        datadir = pathlib.Path(__file__).parent / ".." / ".." / "data"
        excelfile = pathlib.Path(datadir) / "cosmos_table4.xls"
        table4 = Table4(excelfile)
        ffmt = cfmt_to_ffmt(INT_FMT, NUM_INT_COLS)
        self.start_line = (
            f"{NUM_INT_VALUES:4d} Integer-header values follow on "
            f"{NUM_INT_ROWS:3d} lines, Format= ({ffmt})"
        )
        self.start_line += (80 - len(self.start_line)) * " "

        # fill in data for int header
        self.header = np.ones((NUM_INT_ROWS, NUM_INT_COLS)) * MISSING_DATA_INT

        units = "counts"
        # if volume in [Volume.CONVERTED, Volume.PROCESSED]:
        #     units = UNIT_TYPES[trace.stats.standard.units_type]
        if volume in [Volume.CONVERTED, Volume.PROCESSED]:
            units = trace.stats.standard.units_type

        # Data/File Parameters
        # Note that notation here is that the indices indicate row/column number as
        # described in the COSMOS documentation.
        self.header[0][0] = volume.value
        self.header[0][1] = TABLE1[trace.stats.standard.units_type]
        self.header[0][2] = TABLE2[units]
        self.header[0][3] = int(COSMOS_FORMAT * 100)
        self.header[0][4] = SEISMIC_TRIGGER

        # Station Parameters
        self.header[1][0] = table4.get_cosmos_code(
            trace.stats.network
        )  # who runs network?
        self.header[1][1] = table4.get_cosmos_code(
            trace.stats.network
        )  # who owns station?
        stype = trace.stats.standard.structure_type
        if not len(stype):
            stype = "Unspecified"
        self.header[1][8] = REV_BUILDING_TYPES[stype]

        self.header[2][2] = len(stream)

        # Record Parameters
        self.header[3][0] = SOLID_STATE_RECORDING_MEDIUM
        self.header[3][9] = trace.stats.starttime.year
        self.header[4][0] = trace.stats.starttime.julday
        self.header[4][1] = trace.stats.starttime.month
        self.header[4][2] = trace.stats.starttime.day
        self.header[4][3] = trace.stats.starttime.hour
        self.header[4][4] = trace.stats.starttime.minute

        self.header[4][5] = TIME_QUALITY_INDICATOR

        # Sensor/channel Parameters
        channels = [trace.stats.channel for trace in stream]
        channel_number = channels.index(trace.stats.channel) + 1
        self.header[4][9] = channel_number
        azimuth = trace.stats.standard.horizontal_orientation

        # 0 degrees is not an accepted azimuth angle...
        if azimuth == 0.0:
            azimuth = 360.0
        self.header[5][3] = azimuth

        # Filtering/processing parameters
        if volume == Volume.PROCESSED:
            try:
                bp_prov = trace.get_provenance("bandpass_filter")[-1]["prov_attributes"]
                hp_prov = trace.get_provenance("highpass_filter")[-1]["prov_attributes"]
                lp_prov = trace.get_provenance("lowpass_filter")[-1]["prov_attributes"]
                if len(bp_prov["number_of_passes"]) > 0:
                    num_of_passes = bp_prov["number_of_passes"]
                elif len(hp_prov["number_of_passes"]) > 0:
                    num_of_passes = hp_prov["number_of_passes"]
                elif len(lp_prov["number_of_passes"]) > 0:
                    num_of_passes = lp_prov["number_of_passes"]
            except IndexError:
                num_of_passes = 0
            self.header[5][9] = NONCAUSAL_BUTTERWORTH_FILTER
            if num_of_passes == 1:
                self.header[5][9] = CAUSAL_BUTTERWORTH_FILTER
            self.header[6][1] = NONCAUSAL_BUTTERWORTH_FILTER
            if num_of_passes == 1:
                self.header[6][1] = CAUSAL_BUTTERWORTH_FILTER
            self.header[6][3] = FREQ_DOMAIN_FILTER
        # Response spectrum parameters
        self.header[7][4] = NOMINAL_CONSTANTS_FLAG  # 75
        self.header[7][5] = RECORD_PROBLEM_INDICATOR  # 76
        # Miscellaneous

    def write(self, cosmos_file):
        # write out data for int header to cosmos_file object
        cosmos_file.write(self.start_line + "\n")
        fmt = [INT_FMT] * NUM_INT_COLS
        np.savetxt(cosmos_file, self.header, fmt=fmt, delimiter="")


class FloatHeader(object):
    def __init__(
        self,
        trace,
        scalar_event,
        volume,
    ):
        self.volume = volume
        # fill in data for float header
        # fill in data for int header
        ffmt = cfmt_to_ffmt(FLOAT_FMT, NUM_FLOAT_COLS)
        self.start_line = (
            f"{NUM_FLOAT_VALUES:4d} Real-header values follow on "
            f"{NUM_FLOAT_ROWS} lines , Format = ({ffmt})"
        )
        self.header = np.ones((NUM_FLOAT_VALUES)) * MISSING_DATA_FLOAT

        # Station parameters
        self.header[0] = trace.stats.coordinates.latitude  # 1
        self.header[1] = trace.stats.coordinates.longitude  # 2
        self.header[2] = trace.stats.coordinates.elevation  # 3

        # Earthquake parameters
        self.header[9] = scalar_event.latitude  # 10
        self.header[10] = scalar_event.longitude  # 11
        self.header[11] = scalar_event.depth_km  # 12
        self.header[12] = scalar_event.magnitude  # 13
        dist, az, _ = gps2dist_azimuth(
            scalar_event.latitude,
            scalar_event.longitude,
            trace.stats.coordinates.latitude,
            trace.stats.coordinates.longitude,
        )
        self.header[16] = dist / 1000  # 17 - m to km
        self.header[17] = az  # 18

        # Recorder/datalogger parameters
        if hasattr(trace.stats, "data_logger_sensitivity"):
            # volts to counts is counts/volt
            # MICRO_TO_VOLT is microvolts/volt
            # self.header[21] = (
            #     1 / trace.stats.standard.volts_to_counts
            # ) * MICRO_TO_VOLT  # 22 microvolts/count
            self.header[21] = trace.stats.data_logger_sensitivity

        # length of noise and signal windows
        if trace.has_parameter("signal_split"):  # only present in processed data??
            signal_start_time = UTCDateTime(
                trace.get_parameter("signal_split")["split_time"]
            )
            noise_duration_secs = signal_start_time - trace.stats.starttime
            signal_duration_secs = trace.stats.endtime - signal_start_time
            self.header[23] = noise_duration_secs  # 24
            self.header[24] = signal_duration_secs  # 25

        self.header[25] = trace.stats.standard["corner_frequency"]
        # Record parameters
        # dtime = trace.stats.endtime - trace.stats.starttime
        dtime = len(trace.data) * trace.stats.delta
        msec = trace.stats.starttime.second + (trace.stats.starttime.microsecond / 1e6)
        self.header[29] = msec  # 30
        self.header[30] = TIME_CORRECTION  # 31 time correction
        self.header[31] = GMT_OFFSET_HOURS  # 32
        self.header[33] = trace.stats.delta  # 34
        self.header[34] = dtime  # 35

        # Find detrend to put in header:
        dprov = trace.get_provenance("detrend")
        detrend_values = [
            p["prov_attributes"]["value"]
            for p in dprov
            if "value" in p["prov_attributes"]
        ]
        if detrend_values:
            self.header[35] = detrend_values[0]

        # Sensor/channel parameters
        self.header[39] = 1 / trace.stats.standard.instrument_period  # 40
        self.header[40] = trace.stats.standard.instrument_damping  # 41

        if hasattr(trace.stats, "stage_1_sensitivity"):
            self.header[41] = trace.stats.stage_1_sensitivity
        if volume == Volume.PROCESSED:
            self.header[53] = trace.get_parameter("corner_frequencies")["lowpass"]
            self.header[56] = trace.get_parameter("corner_frequencies")["highpass"]

        # time history parameters
        self.header[61] = trace.stats.delta * 1000  # 62 msecs
        self.header[62] = dtime  # 63
        self.header[63] = np.abs(trace.max())  # 64
        maxidx = np.where(trace.data == trace.max())[0][0]
        maxtime = trace.stats.delta * maxidx  # seconds since rec start
        self.header[64] = maxtime  # 65

        self.header[65] = trace.data.mean()  # 66

        # replace nan values with missing code
        self.header[np.isnan(self.header)] = MISSING_DATA_FLOAT

    def write(self, cosmos_file):
        # write out data for float header to cosmos_file object
        # write out data for int header to cosmos_file object
        cosmos_file.write(self.start_line + "\n")
        block1_fmt = [FLOAT_FMT] * NUM_FLOAT_COLS
        header_data = self.header.flatten()[0:100]
        nfullrows = int(len(header_data) / NUM_FLOAT_COLS)
        block1 = header_data[0 : NUM_FLOAT_COLS * nfullrows]
        block1 = block1.reshape((nfullrows, NUM_FLOAT_COLS))
        np.savetxt(cosmos_file, block1, fmt=block1_fmt, delimiter="")
        remainder = len(header_data) % NUM_FLOAT_COLS
        if remainder > 0:
            block2_fmt = [FLOAT_FMT] * remainder
            block2 = header_data[-remainder:].reshape((1, remainder))
            np.savetxt(cosmos_file, block2, fmt=block2_fmt, delimiter="")


class DataBlock(object):
    def __init__(self, trace, volume, eventid, gmprocess_version):
        datadir = pathlib.Path(__file__).parent / ".." / ".." / "data"
        excelfile = pathlib.Path(datadir) / "cosmos_table4.xls"
        table4 = Table4(excelfile)
        self.volume = volume
        self.trace = trace
        quantity = "velocity"
        if trace.stats.standard.units_type == "acc":
            quantity = "acceleration"
        npts = len(trace.data)
        # duration secs
        itime = int(np.round(trace.stats.endtime - trace.stats.starttime))

        if volume == Volume.RAW:
            data_fmt = INT_DATA_FMT
            units = "counts"
        else:
            data_fmt = FLOAT_DATA_FMT
            units = UNIT_TYPES[trace.stats.standard.units_type]

        ffmt = cfmt_to_ffmt(data_fmt, NUM_DATA_COLS)

        # fill in comment fields that we use for overflow information
        self.comment_lines = []
        instrument = trace.stats.standard.instrument.replace("None", "").strip()
        self.write_comment("Sensor", instrument, "standard")
        network = trace.stats.network
        station = trace.stats.station
        channel = trace.stats.channel
        location = trace.stats.location
        if not len(location.strip()):
            location = "--"
        event_network = table4.get_matching_network(eventid)
        eventcode = eventid.lower().replace(event_network, "")
        record_id = (
            f"{event_network.upper()}.{eventcode}.{network}."
            f"{station}.{channel}.{location}"
        )
        self.write_comment("RcrdId", record_id, "standard")
        scnl = f"{station}.{channel}.{network}.{location}"
        tnow_str = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y/%m/%d %H:%M:%S.%f"
        )
        scnl_str = f"{scnl} <AUTH> {tnow_str}"
        self.write_comment("SCNL", scnl_str, "non-standard")
        if self.volume != Volume.RAW:
            pstr = (
                f"Automatically processed using gmprocess version {gmprocess_version}"
            )
            self.write_comment("PROCESS", pstr, "non-standard")
        elif self.volume == Volume.RAW:
            pstr = f"Created using gmprocess version {gmprocess_version}"
            self.write_comment("PROCESS", pstr, "non-standard")
        self.write_comment(
            "eventURL",
            "For updated information about the earthquake visit the URL below:",
            "non-standard",
        )
        self.write_comment(
            "eventURL",
            f"https://earthquake.usgs.gov/earthquakes/eventpage/{eventid}",
            "non-standard",
        )

        # fill in data for float header
        self.start_lines = []
        ncomments = len(self.comment_lines)
        self.header_line1 = (
            f'{ncomments:4d} Comment line(s) follow, each starting with a "|":'
        )
        int_units = None
        if volume == Volume.RAW or volume == Volume.CONVERTED:
            int_units = TABLE2["counts"]
        elif volume == Volume.PROCESSED:
            int_units = TABLE2[trace.stats.standard.units_type]
        elif volume == Volume.SPECTRA:
            int_units = TABLE2["acc"]  # Verify this makes sense
        else:
            raise ValueError("Unknown volume '{volume}' for setting int_units.")
        self.header_line2 = (
            f"{npts:8d} {quantity} pts, approx  {itime} secs, "
            f"units={units.replace('^', '')} ({int_units}),Format=({ffmt})"
        )

    def write_comment(self, key, value, comment_type):
        if comment_type == "standard":
            comment = f"| {key}: {value}"
        else:
            comment = f"|<{key}>{value}"
        # pad to 80 characters
        comment += (80 - len(comment)) * " "
        self.comment_lines.append(comment)
        return

    def write(self, cosmos_file):
        # write out data for float header to cosmos_file object
        cosmos_file.write(self.header_line1 + "\n")
        for line in self.comment_lines:
            cosmos_file.write(line + "\n")
        cosmos_file.write(self.header_line2 + "\n")
        if self.volume != Volume.RAW:
            fmt = [FLOAT_DATA_FMT] * NUM_DATA_COLS
        else:
            fmt = [INT_DATA_FMT] * NUM_DATA_COLS
        data = self.trace.data
        if self.volume == Volume.CONVERTED:
            # counts/m/s^2
            instrument_sensitivity = self.trace.stats.standard.instrument_sensitivity
            data /= instrument_sensitivity
            data *= M_TO_CM  # Convert from m to cm
            data -= data.mean()
            # split_prov = self.trace.get_parameter("signal_split")
            # split_time = split_prov["split_time"]
            # noise = self.trace.copy().trim(endtime=split_time)
            # noise_mean = np.mean(noise.data)

        if self.volume != Volume.SPECTRA:
            data, remainder = split_data(data, NUM_DATA_COLS)
            np.savetxt(cosmos_file, data, fmt=fmt, delimiter="")
            if self.volume != Volume.RAW:
                fmt = [FLOAT_DATA_FMT] * len(remainder.T)
            else:
                fmt = [INT_DATA_FMT] * len(remainder.T)
            if len(remainder[0]):
                np.savetxt(cosmos_file, remainder, fmt=fmt, delimiter="")


def split_data(data, ncols):
    nrows = int(len(data) / ncols)
    npts = nrows * ncols
    tdata = data[0:npts]
    remainder = data[npts:]
    remainder = np.reshape(remainder, (1, len(remainder)))
    tdata = np.reshape(tdata, (nrows, ncols))
    return (tdata, remainder)


class CosmosWriter(object):
    """Class for writing COSMOS files from ASDF/HDF5 workspace files."""

    def __init__(
        self,
        cosmos_directory,
        h5_filename,
        volume=Volume.PROCESSED,
        label=None,
        concatenate_channels=False,
    ):
        """CosmosWriter initialization.

        Args:
            cosmos_directory (str, pathlib.Path):
                Path to write output files.
            h5_filename (str, pathlib.Path):
                Path to HDF5 workspace file.
            volume (Volume):
                COSMOS processing volume level.
            label (str):
                ASDF label.
            concatenate_channels (bool):
                Concatenate channels into one file.
        """
        self._workspace = StreamWorkspace.open(h5_filename)
        self._cosmos_directory = pathlib.Path(cosmos_directory)
        self._volume = volume
        labels = self._workspace.get_labels()
        if label is None:
            if volume == Volume.RAW:
                if "unprocessed" not in labels:
                    msg = f"'unprocessed' label not found in workspace {h5_filename}."
                    raise KeyError(msg)
                label = "unprocessed"
            else:
                labels.remove("unprocessed")
                if len(labels) > 1:
                    raise KeyError(
                        f"More than one processed dataset ({labels}) found in {h5_filename}."
                    )
                label = labels[0]
        else:
            if label not in labels:
                raise KeyError(
                    f"Label ({label}) not found in labels ({labels}) from {h5_filename}."
                )

        self._label = label
        self._concatenate_channels = concatenate_channels

    def write(self):
        nevents = 0
        nstreams = 0
        ntraces = 0
        files = []
        for eventid in self._workspace.get_event_ids():
            nevents += 1
            scalar_event = self._workspace.get_event(eventid)
            gmprocess_version = self._workspace.get_gmprocess_version()
            # remove "dirty" stuff from gmprocess version
            idx = gmprocess_version.find(".dev")
            gmprocess_version = gmprocess_version[0:idx]
            ds = self._workspace.dataset
            station_list = ds.waveforms.list()
            extension = "v0"
            if self._volume == Volume.CONVERTED:
                extension = "v1"
            elif self._volume == Volume.PROCESSED:
                extension = "v2"
            elif self._volume == Volume.SPECTRA:
                extension = "v3"
                wmc = WaveformMetricCollection.from_workspace(
                    self._workspace, "default"
                )
            for station_id in station_list:
                streams = self._workspace.get_streams(
                    eventid, stations=[station_id], labels=[self._label]
                )
                has_data = False
                for stream in streams:
                    if not stream.passed:
                        continue
                    logging.info(f"Writing stream {stream.id}...")
                    nstreams += 1
                    cosmos_file = None
                    inv = stream.get_inventory()
                    if inv is None:
                        msg = (
                            f"Stream {stream} is missing StationXML inventory object and so "
                            "unknown -999 values will be used in the header for instrument sensitivity "
                            "and data logger sensitivity in the COSMOS headers "
                        )
                        logging.info(msg)
                    net = stream[0].stats.network
                    sta = stream[0].stats.station
                    loc = stream[0].stats.location
                    dashes = "-" * (5 - len(sta))
                    if self._concatenate_channels:
                        cosmos_file = io.StringIO()
                        if self._volume == Volume.RAW:
                            # strip origin code from event id
                            event_code = eventid[2:]
                            fname = f"{net}{sta}{dashes}n.{event_code}.{extension}c"
                        else:
                            fname = (
                                f"{net}{sta}{dashes}n.{eventid}.{extension.upper()}c"
                            )
                        cosmos_filename = self._cosmos_directory / fname
                        files.append(cosmos_filename)
                    ichannel = 1
                    if self._volume == Volume.SPECTRA:
                        channels = [tr.stats.channel for tr in stream]
                        _, reverse_dict = component_to_channel(channels)
                    for trace_idx, trace in enumerate(stream):
                        net = trace.stats.network
                        sta = trace.stats.station
                        cha = trace.stats.channel
                        loc = trace.stats.location
                        # COSMOS files will have trace.stats.format_specific,
                        # miniseed/stationxml will not.
                        if trace.stats.format_specific:
                            trace.stats["stage_1_sensitivity"] = (
                                trace.stats.format_specific["stage_1_sensitivity"]
                            )
                            trace.stats["data_logger_sensitivity"] = (
                                trace.stats.format_specific["data_logger_sensitivity"]
                            )
                        else:
                            # Do somthing with StationXML information
                            tinv = inv.select(
                                network=trace.stats.network,
                                station=trace.stats.station,
                                channel=trace.stats.channel,
                                location=trace.stats.location,
                                time=trace.stats.starttime,
                            )
                            stages = tinv[0][0][0].response.response_stages
                            instrument_sensitivity, data_logger_sensitivity = 1, 1
                            for idx, stage in enumerate(stages):
                                if idx == 0:
                                    instrument_sensitivity = stage.stage_gain
                                else:
                                    data_logger_sensitivity *= stage.stage_gain
                            trace.stats["stage_1_sensitivity"] = instrument_sensitivity
                            trace.stats["data_logger_sensitivity"] = (
                                data_logger_sensitivity
                            )

                        if trace.stats.standard.units_type != "acc":
                            msg = (
                                "Only supporting acceleration data at this time. "
                                f"Skipping channel {cha}."
                            )
                            logging.info(msg)
                            continue
                        has_data = True
                        ntraces += 1
                        event_code = eventid[2:]
                        if not self._concatenate_channels:
                            units = trace.stats.standard.units_type
                            if self._volume == Volume.RAW:
                                # strip origin code from event id
                                fname = f"{net}{sta}{dashes}n.{event_code}.{cha}.{loc}.{extension}c"
                            elif self._volume == Volume.CONVERTED:
                                fname = f"{net}{sta}{dashes}n.{event_code}.{cha}.{loc}.{extension.upper()}c"
                            elif self._volume == Volume.PROCESSED:
                                fname = f"{net}{sta}{dashes}n.{event_code}.{cha}.{loc}.{units}.{extension.upper()}c"
                            else:
                                fname = f"{net}{sta}{dashes}n.{event_code}.{cha}.{loc}.{extension.upper()}c"
                            cosmos_filename = self._cosmos_directory / fname
                            files.append(cosmos_filename)
                            cosmos_file = open(cosmos_filename, "wt")
                        if self._volume != Volume.SPECTRA:
                            self._write_data(
                                cosmos_file,
                                eventid,
                                trace,
                                scalar_event,
                                stream,
                                gmprocess_version,
                            )
                        if self._volume == Volume.PROCESSED:
                            config = self._workspace.config
                            vel = get_vel(trace.copy(), config=config)
                            disp = get_disp(trace.copy(), config=config)
                            if self._concatenate_channels:
                                self._write_data(
                                    cosmos_file,
                                    eventid,
                                    vel,
                                    scalar_event,
                                    stream,
                                    gmprocess_version,
                                )
                                self._write_data(
                                    cosmos_file,
                                    eventid,
                                    disp,
                                    scalar_event,
                                    stream,
                                    gmprocess_version,
                                )
                            else:
                                fname_vel = f"{net}{sta}{dashes}n.{event_code}.{cha}.{loc}.vel.{extension.upper()}c"
                                fname_disp = f"{net}{sta}{dashes}n.{event_code}.{cha}.{loc}.dis.{extension.upper()}c"
                                cosmos_file_vel = self._cosmos_directory / fname_vel
                                cosmos_file_disp = self._cosmos_directory / fname_disp
                                files.append(cosmos_file_vel)
                                files.append(cosmos_file_disp)
                                with (
                                    open(cosmos_file_vel, "wt") as f_vel,
                                    open(cosmos_file_disp, "wt") as f_disp,
                                ):
                                    self._write_data(
                                        f_vel,
                                        eventid,
                                        vel,
                                        scalar_event,
                                        stream,
                                        gmprocess_version,
                                    )
                                    self._write_data(
                                        f_disp,
                                        eventid,
                                        disp,
                                        scalar_event,
                                        stream,
                                        gmprocess_version,
                                    )
                                    end_record = f"End-of-data for Chan{cha}\n"
                                    f_vel.write(end_record)
                                    f_disp.write(end_record)

                        elif self._volume == Volume.SPECTRA:

                            # Sould we write out FAS? (regular array, so periods will not match)
                            if trace_idx == 0:
                                self._write_data(
                                    cosmos_file,
                                    eventid,
                                    trace,
                                    scalar_event,
                                    stream,
                                    gmprocess_version,
                                )
                                dv = self._workspace.config["metrics"][
                                    "type_parameters"
                                ]["sa"]["damping"]
                                periods = self._workspace.config["metrics"][
                                    "type_parameters"
                                ]["sa"]["periods"]
                                cosmos_file.write(
                                    f"{len(dv)} damping values for which spectra are computed:{dv}\n"
                                    f"{len(periods)} periods at which spectra computed, units= sec(01), Format=({FLOAT_DATA_FMT})\n"
                                    "",
                                )
                                np.savetxt(
                                    cosmos_file,
                                    periods,
                                    fmt=FLOAT_DATA_FMT,
                                )
                            channel = reverse_dict[cha].lower()
                            for metric in ["SD", "SV", "SA"]:
                                for damping in dv:
                                    if metric == "SD":
                                        units = "cm"
                                    elif metric == "SV":
                                        units = "cm/s"
                                    elif metric == "SA":
                                        units = "cm/s^2"
                                    cosmos_file.write(
                                        f"{len(periods)} values of {metric} for Damping={damping}, units={units},Format={FLOAT_DATA_FMT}\n"
                                    )
                                    tmp_df = (
                                        wmc.waveform_metrics[0]
                                        .select(f"{metric}")
                                        .to_df()
                                    )
                                    tmp_df = tmp_df.loc[
                                        tmp_df["IMC"]
                                        == f"Channels(component={channel})"
                                    ]
                                    np.savetxt(
                                        cosmos_file,
                                        tmp_df["Result"].to_numpy(),
                                        fmt=SPECTRA_DATA_FMT,
                                    )

                        end_record = f"End-of-data for Chan{cha}\n"
                        cosmos_file.write(end_record)

                        ichannel += 1
                        if not self._concatenate_channels:
                            cosmos_file.close()
                            cosmos_file = None

                    if self._concatenate_channels:
                        if not has_data:
                            logging.info(
                                f"{station_id} has no acceleration data, no file written."
                            )
                            continue
                        with open(cosmos_filename, "wt") as f:
                            cosmos_file.seek(0)
                            f.write(cosmos_file.getvalue())

        if ntraces:
            logging.debug("{ntraces} written to disk.")
        else:
            logging.info("No traces processed.")
        return (files, nevents, nstreams, ntraces)

    def _write_data(
        self,
        cosmos_file,
        eventid,
        trace,
        scalar_event,
        stream,
        gmprocess_version,
    ):
        logging.debug(f"Getting text header for {trace.id}")
        text_header = TextHeader(
            trace,
            scalar_event,
            stream,
            self._volume,
            self._workspace.config,
        )
        logging.debug(f"Getting int header for {trace.id}")
        int_header = IntHeader(
            trace,
            scalar_event,
            stream,
            self._volume,
            gmprocess_version,
        )
        logging.debug(f"Getting float header for {trace.id}")
        float_header = FloatHeader(
            trace,
            scalar_event,
            self._volume,
        )
        text_header.write(cosmos_file)
        int_header.write(cosmos_file)
        float_header.write(cosmos_file)
        logging.debug(f"Getting data block for {trace.id}")

        data_block = DataBlock(trace, self._volume, eventid, gmprocess_version)
        data_block.write(cosmos_file)

    def __del__(self):
        self._workspace.close()
