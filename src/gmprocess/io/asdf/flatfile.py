"""Module for creating a flatfile from the ASDF file."""

import re
import logging

import pandas as pd
import numpy as np
import scipy.interpolate as spint
from ruamel.yaml import YAML

from gmprocess.utils.config import update_dict, get_config
from gmprocess.utils import constants
from gmprocess.io.asdf import flatfile_constants as flat_const
from gmprocess.metrics.waveform_metric_collection import (
    WaveformMetricCollection,
)
from gmprocess.metrics.station_metric_collection import StationMetricCollection
from gmprocess.metrics.utils import component_to_channel


class Flatfile(object):
    """Class for creating flatfiles from a StreamWorkspace."""

    def __init__(self, workspace, label="default"):
        """Initialize the Flatfile class.

        Args:
            workspace (StreamWorkspace):
                A StreamWorkspace object.
            label (str):
                Processing label.
        """
        self.workspace = workspace
        self.event_info = []
        self.imc_tables = {}
        self.imtlist = []

        # Attribute that is set temporarily in this class
        self._station_metrics = None

        if "WaveFormMetrics" not in self.workspace.dataset.auxiliary_data:
            logging.warning("No WaveFormMetrics found. Cannot build flatfiles.")
        else:
            self.label = label
            self.set_event_info()
            self.set_imc_tables()
            self.get_fit_spectra_table()

    def set_event_info(self):
        """Get a list of event info.

        Populates self.event_info.
        """
        for eventid in self.workspace.get_event_ids():
            event = self.workspace.get_event(eventid)
            self.event_info.append(
                {
                    "id": eventid,
                    "time": event.time,
                    "latitude": event.latitude,
                    "longitude": event.longitude,
                    "depth": event.depth_km,
                    "magnitude": event.magnitude,
                    "magnitude_type": event.magnitude_type,
                }
            )

    def set_imc_tables(self):
        """Construct the IMC tables.

        Populates self.imc_tables, which is a dictionary with keys corresponding to the
        IMC (intensity metric component) and the values are lists of dictionaries in
        which each dictionary is a row for the IMT (intensity metric type) tables.
        """
        if hasattr(self.workspace, "config"):
            config = self.workspace.config
            default_config_file = constants.DATA_DIR / constants.CONFIG_FILE_PRODUCTION
            with open(default_config_file, "r", encoding="utf-8") as f:
                yaml = YAML()
                yaml.preserve_quotes = True
                default_config = yaml.load(f)
            update_dict(self.workspace.config, default_config)
        else:
            config = get_config()
        any_trace_failures = config["check_stream"]["any_trace_failures"]
        use_array = not config["read"]["use_streamcollection"]

        wmc = WaveformMetricCollection.from_workspace(self.workspace, self.label)
        smc = StationMetricCollection.from_workspace(self.workspace)
        for wml, stream_meta, station_metrics in zip(
            wmc.waveform_metrics, wmc.stream_metadata, smc.station_metrics
        ):
            if not wml.metric_list:
                continue

            self._station_metrics = station_metrics
            passed_traces = [tr_met for tr_met in stream_meta if tr_met["passed"]]

            n_passed = len(passed_traces)
            for tr in passed_traces:
                tr.update({"use_array": use_array})

            if any_trace_failures:
                if n_passed < 3:
                    stream_passed = False
                else:
                    stream_passed = True
            else:
                if n_passed:
                    stream_passed = True
                else:
                    stream_passed = False
            if not stream_passed:
                continue

            wm_df = wml.to_df()
            self.imclist = list(set(wm_df["IMC"]))
            self.imtlist = np.unique(wm_df["IMT"]).tolist()
            self.imtlist.sort(key=_natural_keys)

            for imc in self.imclist:  # if "FAS" SAVE
                if str(imc) not in self.imc_tables:
                    self.imc_tables[str(imc)] = []
                row = self.get_imt_row(passed_traces, wml, imc)
                if not row:
                    continue
                self.imc_tables[str(imc)].append(row)  #

    def get_imt_row(self, passed_traces, wml, imc):
        """Get one row of the IMT flatfile fom a stream.

        Args:
            passed_traces (list):
                List dictionaries containing metadata for the passed traces.
            wml (WaveformMetricList):
                A WaveformMetricList object.
            imc (WaveformMetricComponent):
                The intensity metric component.
        """
        row = {}
        trace_meta = passed_traces[0]
        event_dict = self.get_event_dict()
        sta_dict = self.get_sta_dict()
        rec_dict = self.get_record_dict(trace_meta)

        # Add the filter frequency information to the row
        filter_dict = self.get_filter_dict(passed_traces, imc)
        row.update(event_dict)
        row.update(sta_dict)
        row.update(rec_dict)
        row.update(filter_dict)

        wm_df = wml.to_df()
        wm_df = wm_df.loc[wm_df["IMC"] == str(imc)]
        imts = wm_df["IMT"].tolist()
        imt_vals = wm_df["Result"].tolist()
        for imt, val in zip(imts, imt_vals):
            if imt.startswith("FAS("):
                for idx, freq in enumerate(val.frequency):
                    value = val.fourier_spectra[idx]
                    row.update({f"FAS(f={freq}, {imt.split('(')[1]}": value})
            else:
                row.update({imt: val})
        return row

    def get_record_dict(self, trace_meta):
        """Get a dictionary with record info formatted for the flatfile."""
        source_file = (
            trace_meta["standard"]["source_file"]
            if "source_file" in trace_meta["standard"]
            else ""
        )
        return {
            "Network": trace_meta["network"],
            "DataProvider": trace_meta["source"],
            "StationCode": trace_meta["station"],
            "StationDescription": trace_meta["station_name"],
            "StationLatitude": trace_meta["latitude"],
            "StationLongitude": trace_meta["longitude"],
            "StationElevation": trace_meta["elevation"],
            "SamplingRate": trace_meta["sampling_rate"],
            "SourceFile": source_file,
        }

    def get_sta_dict(self):
        """Get a dictionary with station info formatted for the flatfile."""
        return {
            "BackAzimuth": self._station_metrics.back_azimuth,
            "EpicentralDistance": self._station_metrics.repi,
            "HypocentralDistance": self._station_metrics.rhyp,
            "RuptureDistance": self._station_metrics.rrup_mean,
            "RuptureDistanceVar": self._station_metrics.rrup_var,
            "JoynerBooreDistance": self._station_metrics.rjb_mean,
            "JoynerBooreDistanceVar": self._station_metrics.rjb_var,
            "GC2_ry": self._station_metrics.gc2_ry,
            "GC2_rx": self._station_metrics.gc2_rx,
            "GC2_ry0": self._station_metrics.gc2_ry0,
            "GC2_U": self._station_metrics.gc2_U,
            "GC2_T": self._station_metrics.gc2_T,
        }

    def get_event_dict(self):
        """Get a dictionary with event info formatted for the flatfile."""
        # currently only support one event per workspace file
        event_info = self.event_info[0]

        return {
            "EarthquakeId": event_info["id"],
            "EarthquakeTime": event_info["time"],
            "EarthquakeLatitude": event_info["latitude"],
            "EarthquakeLongitude": event_info["longitude"],
            "EarthquakeDepth": event_info["depth"],
            "EarthquakeMagnitude": event_info["magnitude"],
            "EarthquakeMagnitudeType": event_info["magnitude_type"],
        }

    def get_filter_dict(self, passed_traces, imc):
        """Get the filter corner frequency dictionary (and also deal with station id).

        This became a very confusing method becuse of the bandaids we had to add to
        support the "use_array" use-case.

        Args:
            passed_traces (list):
                List of dictionaries containing metadata for the passed traces.
            imc (WaveformMetricComponent):
                The intensity metric component.
        """
        # Sort out station id
        tr_met = passed_traces[0]
        base_station_id = ".".join(
            [tr_met["network"], tr_met["station"], tr_met["location"]]
        )
        if tr_met["use_array"]:
            station_id = ".".join([base_station_id, tr_met["channel"]])
        else:
            station_id = ".".join([base_station_id, tr_met["channel"][0:2]])

        # Deal with channel vs simpler component names
        channels = [pt["channel"] for pt in passed_traces]
        _, chan2comp = component_to_channel(channels)
        components = []
        for chan in channels:
            components.append(chan2comp[chan])

        filter_dict = {
            "StationID": station_id,
        }
        for comp, meta in zip(components, passed_traces):
            lp_key = f"{comp}Lowpass"
            hp_key = f"{comp}Highpass"
            filter_dict[lp_key] = (
                meta["lowpass_filter"] if "lowpass_filter" in meta else np.nan
            )
            filter_dict[hp_key] = (
                meta["highpass_filter"] if "highpass_filter" in meta else np.nan
            )

        return filter_dict

    def get_tables(self):
        """Retrieve dataframes containing event information and IMC/IMT metrics.

        Returns:
            tuple: Elements are:
                   - pandas DataFrame containing event information,
                   - dictionary of DataFrames, where keys are IMCs.
                   - dictionary of README DataFrames, where keys are IMCs.
        """
        readme_tables = {}

        for key, table in self.imc_tables.items():
            table = pd.DataFrame.from_dict(table)
            imt_cols = list(set(table.columns) & set(self.imtlist))

            # Remove FAS?
            fas_cols = [c for c in imt_cols if c.startswith("FAS(")]
            fas_df = table[fas_cols]
            if pd.isna(fas_df).all(axis=None):
                imt_cols = [x for x in imt_cols if x not in fas_cols]
            imt_cols.sort(key=_natural_keys)

            non_imt_cols = [col for col in table.columns if col not in self.imtlist]
            table = table[non_imt_cols + imt_cols]
            self.imc_tables[key] = table
            readme_dict = {}
            for col in table.columns:
                if col in flat_const.FLATFILE_COLUMNS:
                    readme_dict[col] = flat_const.FLATFILE_COLUMNS[col]
                else:
                    imt = col.upper()
                    if imt.startswith("SA"):
                        readme_dict["SA(X)"] = flat_const.FLATFILE_IMT_COLUMNS["SA(X)"]
                    elif imt.startswith("PSA"):
                        readme_dict["PSA(X)"] = flat_const.FLATFILE_IMT_COLUMNS[
                            "PSV(X)"
                        ]
                    elif imt.startswith("SV"):
                        readme_dict["SV(X)"] = flat_const.FLATFILE_IMT_COLUMNS["SV(X)"]
                    elif imt.startswith("PSV"):
                        readme_dict["PSV(X)"] = flat_const.FLATFILE_IMT_COLUMNS[
                            "PSV(X)"
                        ]
                    elif imt.startswith("SD"):
                        readme_dict["SD(X)"] = flat_const.FLATFILE_IMT_COLUMNS["SD(X)"]
                    elif imt.startswith("FAS"):
                        readme_dict["FAS(X)"] = flat_const.FLATFILE_IMT_COLUMNS[
                            "FAS(X)"
                        ]
                    elif imt.startswith("DURATION"):
                        readme_dict["DURATIONp-q"] = flat_const.FLATFILE_IMT_COLUMNS[
                            "DURATIONp-q"
                        ]
                    else:
                        readme_dict[imt] = flat_const.FLATFILE_IMT_COLUMNS[imt]
            df_readme = pd.DataFrame.from_dict(readme_dict, orient="index")
            df_readme.reset_index(level=0, inplace=True)
            df_readme.columns = ["Column header", "Description"]
            readme_tables[key] = df_readme

        event_table = pd.DataFrame.from_dict(self.event_info)
        return (event_table, self.imc_tables, readme_tables)

    def get_fit_spectra_table(self):
        """Returns a tuple of two pandas DataFrames. The first contains the fit_spectra
        parameters for each trace in the workspace matching eventid and label. The
        second is a README describing each column in the first DataFrame.


        Returns:
            tuple: The fit spectra dataframe, and a README dataframe.
        """
        # List that will hold a dictionary for each row of the table
        fit_table = []

        event_dict = self.get_event_dict()

        station_list = self.workspace.dataset.waveforms.list()
        for station_id in station_list:
            streams = self.workspace.get_streams(
                event_dict["EarthquakeId"],
                stations=[station_id],
                labels=[self.label],
                config=self.workspace.config,
            )

            for stream in streams:
                if not stream.passed:
                    continue
                for trace in stream:
                    if trace.has_parameter("fit_spectra"):
                        fit_dict = trace.get_parameter("fit_spectra")
                        fit_dict.update(event_dict)
                        fit_dict["TraceID"] = trace.id
                        coords = trace.stats.coordinates
                        fit_dict["StationLatitude"] = coords.latitude
                        fit_dict["StationLongitude"] = coords.longitude
                        fit_dict["StationElevation"] = coords.elevation
                        if trace.has_parameter("corner_frequencies"):
                            freq_dict = trace.get_parameter("corner_frequencies")
                            fit_dict["fmin"] = freq_dict["highpass"]
                            fit_dict["fmax"] = freq_dict["lowpass"]
                        fit_table.append(fit_dict)

        if fit_table:
            fit_df = pd.DataFrame.from_dict(fit_table)
        else:
            return (None, None)

        # Ensure that the DataFrame columns are ordered correctly
        fit_df = fit_df[flat_const.FIT_SPECTRA_COLUMNS.keys()]

        readme = pd.DataFrame.from_dict(flat_const.FIT_SPECTRA_COLUMNS, orient="index")
        readme.reset_index(level=0, inplace=True)
        readme.columns = ["Column header", "Description"]

        return (fit_df, readme)

    def get_snr_table(self):
        """
        Returns a tuple of two pandas DataFrames. The first contains the
        fit_spectra parameters for each trace in the workspace matching
        eventid and label. The second is a README describing each column
        in the first DataFrame.

        Returns:
            tuple of pandas DataFrames, which consists of the SNR dataframe and its
            associated readme.
        """
        periods = np.array(
            self.workspace.config["metrics"]["type_parameters"]["sa"]["periods"]
        )

        # List that will hold a dictionary for each row of the table
        snr_table = []

        event_dict = self.get_event_dict()

        station_list = self.workspace.dataset.waveforms.list()
        for station_id in station_list:
            streams = self.workspace.get_streams(
                event_dict["EarthquakeId"],
                stations=[station_id],
                labels=[self.label],
                config=self.workspace.config,
            )

            for stream in streams:
                if not stream.passed:
                    continue
                for trace in stream:
                    if trace.has_cached("snr"):
                        snr_dict = self.__flatten_snr_dict(trace, periods)
                        snr_dict.update(event_dict)
                        snr_dict["TraceID"] = trace.id
                        coords = trace.stats.coordinates
                        snr_dict["StationLatitude"] = coords.latitude
                        snr_dict["StationLongitude"] = coords.longitude
                        snr_dict["StationElevation"] = coords.elevation
                        snr_table.append(snr_dict)

        if snr_table:
            snr_df = pd.DataFrame.from_dict(snr_table)
        else:
            snr_df = pd.DataFrame(columns=flat_const.SNR_COLUMNS.keys())

        # Ensure that the DataFrame columns are ordered correctly
        df1 = pd.DataFrame()
        df2 = pd.DataFrame()
        for col in snr_df.columns:
            if col in flat_const.SNR_COLUMNS:
                df1[col] = snr_df[col]
            else:
                df2[col] = snr_df[col]
        df1 = df1[flat_const.SNR_COLUMNS.keys()]
        df_final = pd.concat([df1, df2], axis=1)

        readme = pd.DataFrame.from_dict(
            {**flat_const.SNR_COLUMNS, **flat_const.SNR_FREQ_COLUMNS},
            orient="index",
        )
        readme.reset_index(level=0, inplace=True)
        readme.columns = ["Column header", "Description"]

        return (df_final, readme)

    @staticmethod
    def __flatten_snr_dict(tr, periods):
        freq = np.sort(1.0 / periods)
        tmp_dict = tr.get_cached("snr")
        interp = spint.interp1d(
            tmp_dict["freq"],
            np.clip(tmp_dict["snr"], 0, np.inf),
            kind="linear",
            copy=False,
            bounds_error=False,
            fill_value=np.nan,
            assume_sorted=True,
        )
        snr = interp(freq)
        snr_dict = {}
        for f, s in zip(freq, snr):
            key = f"SNR({f:.4g})"
            snr_dict[key] = s
        return snr_dict


def _natural_keys(text):
    """
    Helper function for sorting IMT list. This is needed because using the
    plain .sort() will put SA(10.0) before SA(2.0), for example.
    """
    return [_atof(c) for c in re.split(r"[+-]?([0-9]+(?:[.][0-9]*)?|[.][0-9]+)", text)]


def _atof(text):
    try:
        retval = float(text)
    except ValueError:
        retval = text
    return retval
