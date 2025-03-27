"""Module for interacting with the workspace HDF file."""

import copy
import importlib.metadata
import io
import json
import logging
import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyasdf
from gmprocess.core import provenance
from gmprocess.core.scalar_event import ScalarEvent
from gmprocess.core.stationstream import StationStream
from gmprocess.core.stationtrace import StationTrace
from gmprocess.core.streamarray import StreamArray
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.io.asdf import workspace_constants as wc
from gmprocess.io.asdf.path_utils import (
    get_stream_name,
    get_stream_path,
    get_trace_name,
    get_trace_path,
)
from gmprocess.utils import constants
from gmprocess.utils.config import get_config, update_dict
from gmprocess.utils.config_versioning import config_from_v1, get_config_version
from h5py.h5py_warnings import H5pyDeprecationWarning
from obspy.core.utcdatetime import UTCDateTime
from ruamel.yaml import YAML

TIMEFMT_MS = "%Y-%m-%dT%H:%M:%S.%fZ"

VERSION = importlib.metadata.version("gmprocess")


class StreamWorkspace(object):
    """Class for interacting with the ASDF file."""

    def __init__(self, filename, compression=None):
        """Create an ASDF file given an Event and list of StationStreams.

        Args:
            filename (str or pathlib.Path):
                Path to ASDF file to create.
            compression (str):
                Any value supported by pyasdf.asdf_data_set.ASDFDataSet.
        """
        filename = Path(filename)

        if filename.is_file():
            self.dataset = pyasdf.ASDFDataSet(filename)
        else:
            self.dataset = pyasdf.ASDFDataSet(filename, compression=compression)
        self.filename = filename
        self.format_version = wc.FORMAT_VERSION

        # Add the config data as workspace attribute if it is present
        group_name = "config/config"
        config_exists = group_name in self.dataset._auxiliary_data_group
        if config_exists:
            self.set_config()

    @classmethod
    def create(cls, filename, compression=None):
        """Create a new ASDF file.

        Args:
            filename (str or pathlib.Path):
                Path to existing ASDF file.
            compression (str):
                Any value supported by pyasdf.asdf_data_set.ASDFDataSet.

        Returns:
            StreamWorkspace: Object containing ASDF file.
        """
        filename = Path(filename)

        if filename.is_file():
            raise IOError(f"File {filename} already exists.")
        return cls(filename)

    @classmethod
    def open(cls, filename):
        """Load from existing ASDF file.

        Args:
            filename (str or pathlib.Path):
                Path to existing ASDF file.

        Returns:
            StreamWorkspace: Object containing ASDF file.
        """
        filename = Path(filename)

        if not filename.is_file():
            raise IOError(f"File {filename} does not exist.")
        return cls(filename)

    def close(self):
        """Close the workspace."""
        del self.dataset

    def __repr__(self):
        """Provide summary string representation of the file.

        Returns:
            str: Summary string representation of the file.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=H5pyDeprecationWarning)
            fmt = "Events: %i Stations: %i Streams: %i"
            nevents = len(self.dataset.events)
            stations = []
            nstreams = 0
            for waveform in self.dataset.waveforms:
                inventory = waveform["StationXML"]
                nstreams += len(waveform.get_waveform_tags())
                for station in inventory.networks[0].stations:
                    stations.append(station.code)
            stations = set(stations)
            nstations = len(stations)
        return fmt % (nevents, nstations, nstreams)

    def add_event(self, event):
        """Add event object to file.

        Args:
            event (Event): Obspy event object.
            strec (dict): STREC results.
        """
        self.dataset.add_quakeml(event)

    def add_rupture(self, rupture, event_id, label):
        """Inserts information from the rupture model into the workspace.

        Args:
            rupture (dict):
                Rupture model.
            event_id (str):
                Event id.
            label (str):
                Process label, user can input this from gmrecords assemble subcommand,
                "default" if no input.
        """
        cells = np.array(rupture.cells)
        vertices = np.array(rupture.vertices)
        description = rupture.description
        reference = rupture.reference

        rupture_path = f"{event_id}_{label}"

        self.dataset.add_auxiliary_data(
            cells,
            data_type="RuptureModels",
            path=rupture_path + "/Cells",
            parameters={},
        )
        self.dataset.add_auxiliary_data(
            vertices,
            data_type="RuptureModels",
            path=rupture_path + "/Vertices",
            parameters={},
        )
        self.insert_aux(
            description,
            data_name="RuptureModels",
            path=rupture_path + "/Description",
        )
        self.insert_aux(
            reference, data_name="RuptureModels", path=rupture_path + "/Reference"
        )

    def get_rupture(self, event_id, label="default"):
        """Retrieves cells, vertices, description, and reference for a rupture.

        Args:
            event_id (str):
                Event id.
            label (str):
                Process label, "default" if no input.
        Returns:
            dict: Keys are cells, vertices, description, and reference.

            Cells and vertices are numpy arrays. The Vertices dataset is
            a 2D array [#vertices, spaceDim] where spaceDim=3. The Cells
            dataset is a 2D array [#cells, #corners] where #corners is
            the number of vertices in a cell. In general, we will have
            quadrilaterals (#corners=4) or triangles (#corners=3).
        """
        aux_data = self.dataset.auxiliary_data

        if "RuptureModels" not in aux_data:
            return None

        dset_name = f"{event_id}_{label}"
        if dset_name in aux_data["RuptureModels"]:
            rupture_model = aux_data["RuptureModels"][dset_name]
        else:
            raise ValueError(
                f"Could not find a rupture model with event id '{event_id}' "
                f"and label '{label}."
            )

        cells = rupture_model["Cells"].data
        cells = np.array(cells)

        vertices = rupture_model["Vertices"].data
        vertices = np.array(vertices)

        description = array_to_str(rupture_model["Description"].data)
        reference = array_to_str(rupture_model["Reference"].data)

        rup_dict = {
            "cells": cells,
            "vertices": vertices,
            "description": description,
            "reference": reference,
        }

        return rup_dict

    def add_strec(self, strec, event_id):
        """Add STREC results to auxiliary data.

        Args:
            strec (dict):
                STREC results.
            event_id (str):
                Event id.
        """
        strec_params_str = dict_to_str(strec.results)
        dtype = "StrecParameters"
        strec_path = f"STREC/{event_id}"
        self.insert_aux(strec_params_str, dtype, strec_path, True)

    def get_strec(self, event_id):
        """Get STREC results from auxiliary data"""
        aux_data = self.dataset.auxiliary_data
        if "StrecParameters" not in aux_data:
            return None
        jsonstr = array_to_str(aux_data["StrecParameters"]["STREC"][event_id].data[:])
        jdict = json.loads(jsonstr)
        return jdict

    def add_config(self, config=None, force=False):
        """Add config to an ASDF dataset and workspace attribute.

        Args:
            config (dict):
                Configuration options.
            force (bool):
                Add/overwrite config if it already exists.
        """
        group_name = "config/config"
        data_exists = group_name in self.dataset.auxiliary_data

        if data_exists:
            if force:
                logging.warning("Removing existing conf from workspace.")
                del self.dataset._auxiliary_data_group[group_name]
            else:
                logging.warning(
                    "config already exists in workspace. Set force option to "
                    "True if you want to overwrite."
                )
                return

        if config is None:
            config = get_config()

        self.config = config
        config_bytes = json.dumps(config).encode("utf-8")
        config_array = np.frombuffer(config_bytes, dtype=np.uint8)
        self.dataset.add_auxiliary_data(
            config_array, data_type="config", path="config", parameters={}
        )

    def set_config(self):
        """Get config from ASDF dataset and set as a workspace attribute."""
        group_name = "config/config"
        data_exists = group_name in self.dataset.auxiliary_data
        if not data_exists:
            logging.error("No config found in auxiliary data.")
        bytelist = self.dataset._auxiliary_data_group[group_name][()].tolist()

        # Load config from the workshapce file
        conf_str = "".join([chr(b) for b in bytelist])
        custom_config = json.loads(conf_str)
        conf_version = get_config_version(custom_config)
        if conf_version == 1:
            custom_config = config_from_v1(custom_config)

        # Get the default config
        default_config_file = constants.DATA_DIR / constants.CONFIG_FILE_PRODUCTION
        with open(default_config_file, "r", encoding="utf-8") as f:
            yaml = YAML()
            yaml.preserve_quotes = True
            default_config = yaml.load(f)
        update_dict(default_config, custom_config)
        self.config = default_config

    def add_gmprocess_version(self, version):
        """Add gmprocess version to an ASDF file."""
        self.insert_aux(version, data_name="gmprocess_version", path="version")

    def get_gmprocess_version(self):
        """Get gmprocess version from ASDF file."""
        group_name = "gmprocess_version/version"
        data_exists = group_name in self.dataset.auxiliary_data
        if not data_exists:
            logging.error("No version for gmprocess found.")
        bytelist = self.dataset._auxiliary_data_group[group_name][()].tolist()
        gmprocess_version = "".join([chr(b) for b in bytelist])
        return gmprocess_version

    def get_provenance_records(self, trace_path):
        """Method to get a list of trace provennce records.

        Args:
            trace_path (str):
                Trace path, e.g., "BK.MHC.00.BHE_nc73799091_default".
        """
        if trace_path in self.dataset.provenance:
            provdoc = self.dataset.provenance[trace_path]
        else:
            raise ValueError(f"{trace_path} not in provenance.")
        return provdoc.get_records()

    def get_trace_processing_parameters(self, net_sta, trace_path):
        """Method to get the trace processing parameters.

        Args:
            net_sta (str):
                Network and station code, e.g., "BK.MHC".
            trace_path (str):
                Trace path, e.g., "BK.MHC.00.BHE_nc73799091_default".
        """
        if net_sta in self.dataset.auxiliary_data.TraceProcessingParameters:
            base_aux = self.dataset.auxiliary_data.TraceProcessingParameters[net_sta]
            if trace_path in base_aux:
                bytelist = base_aux[trace_path].data[:].tolist()
                jsonstr = "".join([chr(b) for b in bytelist])
                trace_dict = json.loads(jsonstr)
            else:
                raise ValueError(f"{trace_path} not in TraceProcessingParameters")
        else:
            raise ValueError(f"{net_sta} not in TraceProcessingParameters")
        return trace_dict

    def get_supplemental_stats(self, net_sta, stream_path):
        """Method to get the supplemental stats dictionary for a station.

        Args:
            net_sta (str):
                Network and station code, e.g., "BK.MHC".
            stream_path (str):
                Stream path, e.g., "BK.MHC.00.HN_nc73799091_default".
        """
        if net_sta in self.dataset.auxiliary_data.StreamSupplementalStats:
            base_aux = self.dataset.auxiliary_data.StreamSupplementalStats[net_sta]
            if stream_path in base_aux:
                bytelist = base_aux[stream_path].data[:].tolist()
                jsonstr = "".join([chr(b) for b in bytelist])
                stats_dict = json.loads(jsonstr)
            else:
                raise ValueError(f"{stream_path} not in StreamSupplementalStats")
        else:
            raise ValueError(f"{net_sta} not in StreamSupplementalStats")
        return stats_dict

    def add_streams(
        self,
        event,
        streams,
        label=None,
        gmprocess_version="unknown",
        overwrite=False,
    ):
        """Add a sequence of StationStream objects to an ASDF file.

        Args:
            event (Event):
                Obspy event object.
            streams (list):
                List of StationStream objects.
            label (str):
                Label to attach to stream sequence. Cannot contain an underscore.
            gmprocess_version (str):
                gmprocess version.
            overwrite (bool):
                Overwrite streams if they exist?
        """
        if label is not None:
            if "_" in label:
                raise ValueError("Stream label cannot contain an underscore.")

        # To allow for multiple processed versions of the same Stream
        # let's keep a dictionary of stations and sequence number.
        event_id = self._get_id(event)

        if hasattr(self, "config"):
            config = self.config
        else:
            config = get_config()

        # Level-level provenance entry.
        label_prov = provenance.LabelProvenance(
            label,
            gmprocess_version=VERSION,
            config=config,
        )
        self.dataset.add_provenance_document(
            label_prov.to_provenance_document(), name=label
        )

        for stream in streams:
            logging.info("Adding waveforms for station %s", stream.get_id())
            # is this a raw file? Check the trace for provenance info.
            is_raw = not stream[0].provenance.ids

            if label is None:
                tfmt = "%Y%m%d%H%M%S"
                tnow = UTCDateTime.now().strftime(tfmt)
                label = f"processed{tnow}"
            tag = f"{event_id}_{label}"
            if is_raw:
                level = "raw"
            else:
                level = "processed"

            stream_copy = stream
            if overwrite:
                net_sta = stream.get_net_sta()
                if net_sta in self.dataset.waveforms:
                    if tag in self.dataset.waveforms[net_sta]:
                        # Add stream + traces in dataset not in stream to updated stream
                        stream_copy = stream.copy()
                        stream_trace_ids = set([tr.id for tr in stream])
                        tmp_stream = self.dataset.waveforms[net_sta][tag]
                        for tmp_tr in tmp_stream:
                            if tmp_tr.id not in stream_trace_ids:
                                stream_copy.append(tmp_tr)
                        del self.dataset.waveforms[net_sta][tag]

            self.dataset.add_waveforms(stream_copy, tag=tag, event_id=event_id)

            # add processing provenance info from traces
            if level == "processed":
                provdocs = stream.get_provenance_documents()
                for provdoc, trace in zip(provdocs, stream):
                    trace_name = get_trace_name(trace, tag)
                    self.dataset.add_provenance_document(provdoc, name=trace_name)

            # get the path for the stream for storing aux data
            stream_path = get_stream_path(stream, tag, config)

            # add supplemental stats, e.g., "standard" and "format_specific"
            sup_stats = stream.get_supplemental_stats()
            self.insert_aux(
                dict_to_str(sup_stats),
                "StreamSupplementalStats",
                stream_path,
                overwrite,
            )

            # add processing parameters from streams
            proc_params = {}
            for key in stream.get_stream_param_keys():
                value = stream.get_stream_param(key)
                proc_params[key] = value

            if len(proc_params):
                dtype = "StreamProcessingParameters"
                self.insert_aux(dict_to_str(proc_params), dtype, stream_path, overwrite)

            # add processing parameters from traces
            for trace in stream:
                trace_path = get_trace_path(trace, tag)
                jdict = {}
                for key in trace.get_parameter_keys():
                    value = trace.get_parameter(key)
                    jdict[key] = value
                if len(jdict):
                    dtype = "TraceProcessingParameters"
                    self.insert_aux(dict_to_str(jdict), dtype, trace_path, overwrite)

                # Some processing data is computationally intensive to
                # compute, so we store it in the 'Cache' group.
                for specname in trace.get_cached_names():
                    spectrum = trace.get_cached(specname)
                    # we expect many of these specnames to
                    # be joined with underscores.
                    name_parts = specname.split("_")
                    base_dtype = "".join([part.capitalize() for part in name_parts])
                    for array_name, array in spectrum.items():
                        path = base_dtype + array_name.capitalize() + "/" + trace_path
                        try:
                            group_name = f"Cache/{path}"
                            data_exists = (
                                group_name in self.dataset._auxiliary_data_group
                            )
                            if overwrite and data_exists:
                                del self.dataset._auxiliary_data_group[group_name]
                            self.dataset.add_auxiliary_data(
                                array, data_type="Cache", path=path, parameters={}
                            )
                        except BaseException:
                            pass

            inventory = stream.get_inventory()
            self.dataset.add_stationxml(inventory)

    def get_event_ids(self):
        """Return list of event IDs for events in ASDF file.

        Returns:
            list: List of event_id strings.
        """
        idlist = []
        for event in self.dataset.events:
            eid = event.resource_id.id.replace("smi:local/", "")
            idlist.append(eid)
        return idlist

    def get_labels(self):
        """Return all of the processing labels.

        Returns:
            list: List of processing labels.
        """
        all_tags = []
        for w in self.dataset.waveforms:
            all_tags.extend(w.get_waveform_tags())
        all_labels = list(set([at.split("_")[-1] for at in all_tags]))
        labels = list(set(all_labels))
        return labels

    def get_streams(self, event_id, stations=None, labels=None, config=None):
        """Get Stream from ASDF file given event id and input tags.

        Args:
            event_id (str):
                Event ID corresponding to an Event in the workspace.
            stations (list):
                List of stations (<nework code>.<station code>) to search for.
            labels (list or str):
                List of processing labels to search for.
            config (dict):
                Configuration options.

        Returns:
            StreamCollection: Object containing list of organized
            StationStreams.
        """
        if config is None:
            if hasattr(self, "config"):
                config = self.config
            else:
                config = get_config()

        trace_auxholder = []
        auxdata = self.dataset.auxiliary_data
        streams = []

        if stations is None:
            stations = self.get_stations()
        if labels is None:
            labels = self.get_labels()
        else:
            if not isinstance(labels, list):
                labels = [labels]
            all_labels = self.get_labels()
            for label in labels:
                if label not in all_labels:
                    logging.warning("Label '%s' not found in workspace", label)

        net_codes = [st.split(".")[0] for st in stations]
        sta_codes = [st.split(".")[1] for st in stations]
        tag = [f"{event_id}_{label}" for label in labels]

        for waveform in self.dataset.ifilter(
            self.dataset.q.network == net_codes,
            self.dataset.q.station == sta_codes,
            self.dataset.q.tag == tag,
        ):
            tags = waveform.get_waveform_tags()
            for tag in tags:
                tstream = waveform[tag]

                inventory = waveform["StationXML"]
                for ttrace in tstream:
                    if isinstance(ttrace.data[0], np.floating):
                        if ttrace.data[0].nbytes == 4:
                            ttrace.data = ttrace.data.astype("float32")
                        else:
                            ttrace.data = ttrace.data.astype("float64")
                    else:
                        if ttrace.data[0].nbytes == 2:
                            ttrace.data = ttrace.data.astype("int16")
                        elif ttrace.data[0].nbytes == 4:
                            ttrace.data = ttrace.data.astype("int32")
                        else:
                            ttrace.data = ttrace.data.astype("int64")
                    trace = StationTrace(
                        data=ttrace.data,
                        header=ttrace.stats,
                        inventory=inventory,
                        config=config,
                    )
                    trace_name = get_trace_name(trace, tag)

                    # get the provenance information
                    net_sta = f"{trace.stats.network}.{trace.stats.station}"
                    if trace_name in self.dataset.provenance.list():
                        provdoc = self.dataset.provenance[trace_name]
                        tmp_doc = provenance.TraceProvenance.from_provenance_document(
                            provdoc, trace.stats
                        )
                        for prov_dict in tmp_doc:
                            trace.provenance.append(prov_dict)
                            prov_attr = prov_dict["prov_attributes"]
                            if "output_units" in prov_attr.keys():
                                trace.stats.standard.units = prov_attr["output_units"]
                                try:
                                    trace.stats.standard.units_type = (
                                        constants.REVERSE_UNITS[
                                            prov_attr["output_units"]
                                        ]
                                    )
                                except BaseException:
                                    trace.stats.standard.units_type = "unknown"

                    # get the trace processing parameters
                    if "TraceProcessingParameters" in auxdata:
                        trace_auxholder = auxdata.TraceProcessingParameters
                        if net_sta in trace_auxholder:
                            root_auxholder = trace_auxholder[net_sta]
                            if trace_name in root_auxholder:
                                bytelist = root_auxholder[trace_name].data[:].tolist()
                                jsonstr = "".join([chr(b) for b in bytelist])
                                jdict = json.loads(jsonstr)
                                for key, value in jdict.items():
                                    trace.set_parameter(key, value)

                    # get the trace spectra arrays from auxiliary,
                    # repack into stationtrace object
                    spectra = {}

                    if "Cache" in auxdata:
                        for aux in auxdata["Cache"].list():
                            auxarray = auxdata["Cache"][aux]
                            if net_sta not in auxarray.list():
                                continue
                            auxarray_net_sta = auxarray[net_sta]
                            if trace_name in auxarray_net_sta:
                                specparts = camel_case_split(aux)
                                array_name = specparts[-1].lower()
                                specname = "_".join(specparts[:-1]).lower()
                                specarray = auxarray_net_sta[trace_name].data[()]
                                if specname in spectra:
                                    spectra[specname][array_name] = specarray
                                else:
                                    spectra[specname] = {array_name: specarray}
                        for key, value in spectra.items():
                            trace.set_cached(key, value)

                    # get review information if it is present:
                    if "review" in auxdata:
                        if net_sta in auxdata.review:
                            if trace_name in auxdata.review[net_sta]:
                                tr_review = auxdata.review[net_sta][trace_name]
                                review_dict = {}
                                if "accepted" in tr_review:
                                    tr_acc = tr_review.accepted
                                    review_dict["accepted"] = bool(tr_acc.data[0])
                                    if "timestamp" in tr_acc.parameters:
                                        review_dict["time"] = tr_acc.parameters[
                                            "timestamp"
                                        ]
                                    if "username" in tr_acc.parameters:
                                        review_dict["user"] = tr_acc.parameters[
                                            "username"
                                        ]
                                if "corner_frequencies" in tr_review:
                                    fc_dict = tr_review["corner_frequencies"]
                                    review_dict["corner_frequencies"] = {}
                                    if "highpass" in fc_dict:
                                        review_dict["corner_frequencies"][
                                            "highpass"
                                        ] = fc_dict["highpass"].data[0]
                                    if "lowpass" in fc_dict:
                                        review_dict["corner_frequencies"]["lowpass"] = (
                                            fc_dict["lowpass"].data[0]
                                        )
                                trace.set_parameter("review", review_dict)

                    stream = StationStream(traces=[trace], config=config)
                    stream.tag = tag

                    # deal with stream-level data
                    stream_name = get_stream_name(stream, tag, config)

                    # get the stream processing parameters
                    proc_dict = self._get_aux_dict(
                        "StreamProcessingParameters", net_sta, stream_name
                    )
                    if proc_dict:
                        for key, value in proc_dict.items():
                            stream.set_stream_param(key, value)

                    # get the supplemental stream parameters
                    supp_dict = self._get_aux_dict(
                        "StreamSupplementalStats", net_sta, stream_name
                    )
                    if supp_dict:
                        supp_keys = ["standard", "format_specific"]
                        for supp_key in supp_keys:
                            for key1, value1 in supp_dict.items():
                                if key1 == supp_key:
                                    for key2, value2 in value1.items():
                                        for tr in stream:
                                            tr.stats[supp_key][key2] = value2

                    streams.append(stream)

        # Note: no need to handle duplicates when retrieving stations from the
        # workspace file because it must have been handled before putting them
        # into the workspace file.

        # For backwards compatibility, if use the StreamCollection class if
        # "use_streamcollection" is not set.
        if ("use_streamcollection" not in config["read"]) or config["read"][
            "use_streamcollection"
        ]:
            streams = StreamCollection(streams, handle_duplicates=False, config=config)
        else:
            streams = StreamArray(streams, config=config)
        return streams

    def _get_aux_dict(self, aux_name, net_sta, stream_path):
        """Convenience function to get a diction stored in aux data

        Args:
            aux_name (str):
                Name of data in aux data.
            net_sta (str):
                <net code>.<sta code>.
            stream_path (str):
                <net code>.<sta code>.<loc code>.<chan code>_<event id>_<label>

        Returns:
            dict if found, otherwise None.
        """
        aux_data = self.dataset.auxiliary_data
        if aux_name in aux_data:
            stream_auxholder = aux_data[aux_name][net_sta]
            if stream_path in stream_auxholder:
                auxarray = stream_auxholder[stream_path]
                bytelist = auxarray.data[:].tolist()
                jsonstr = "".join([chr(b) for b in bytelist])
                if len(jsonstr):
                    return json.loads(jsonstr)
                else:
                    return None
        else:
            return None

    def get_stations(self):
        """Get list of station codes within the file.

        Returns:
            list: List of station codes contained in workspace.
        """
        stations = self.dataset.waveforms.list()
        return stations

    def insert_aux(self, data_str, data_name, path, overwrite=False):
        """Insert a string (usually json or xml) into Auxilliary array.

        Args:
            data_str (str):
                String containing data to insert into Aux array.
            data_name (str):
                What this data should be called in the ASDF file.
            path (str):
                The aux path where this data should be stored.
            overwrite (bool):
                Should the data be overwritten if it already exists?
        """
        # this seems like a lot of effort just to store a string in HDF, but other
        # approaches failed. Suggestions are welcome.

        group_name = f"{data_name}/{path}"
        data_exists = group_name in self.dataset._auxiliary_data_group
        if overwrite and data_exists:
            del self.dataset._auxiliary_data_group[group_name]

        data_array = str_to_array(data_str)
        self.dataset.add_auxiliary_data(
            data_array, data_type=data_name, path=path, parameters={}
        )

    def summarize_labels(self):
        """
        Summarize the processing metadata associated with each label in the
        file.

        Returns:
            DataFrame:
                Pandas DataFrame with columns:
                    - Label Processing label.
                    - UserID user id (i.e., jsmith)
                    - UserName Full user name (i.e., Jane Smith) (optional)
                    - UserEmail Email adress (i.e., jsmith@awesome.org)
                      (optional)
                    - Software Name of processing software (i.e., gmprocess)
                    - Version Version of software (i.e., 1.4)

        """
        provtags = self.dataset.provenance.list()
        cols = ["Label", "UserID", "UserName", "UserEmail", "Software", "Version"]
        df = pd.DataFrame(columns=cols, index=None)
        labels = list(set([ptag.split("_")[-1] for ptag in provtags]))
        labeldict = {}
        for label in labels:
            for ptag in provtags:
                if label in ptag:
                    labeldict[label] = ptag
        rows = []
        for label, ptag in labeldict.items():
            row = pd.Series(index=cols, dtype=object)
            row["Label"] = label
            provdoc = self.dataset.provenance[ptag]
            user, software = self._get_agents(provdoc)
            row["UserID"] = user["id"]
            row["UserName"] = user["name"]
            row["UserEmail"] = user["email"]
            row["Software"] = software["name"]
            row["Version"] = software["version"]
            rows.append(row)
        df = pd.DataFrame(rows)
        return df

    def get_inventory(self):
        """Get an Obspy Inventory object from the ASDF file.

        Returns:
            Inventory: Obspy inventory object capturing all of the
                       networks, stations, and channels contained in file.
        """
        inventory = None
        for waveform in self.dataset.waveforms:
            tinv = waveform.StationXML
            if inventory is None:
                inventory = tinv
            else:
                net1 = inventory.networks[0]
                net2 = tinv.networks[0]
                if net1.code == net2.code:
                    for sta in net2.stations:
                        net1.stations.append(copy.deepcopy(sta))
                else:
                    inventory.networks.append(copy.deepcopy(net2))

        return inventory

    def has_event(self, event_id):
        """Verify that the workspace file contains an event matching event_id.

        Args:
            event_id (str):
                ID of event to search for in ASDF file.

        Returns:
            bool: True if event matching ID is found, False if not.
        """
        for event in self.dataset.events:
            if event.resource_id.id.find(event_id) > -1:
                return True
        return False

    def get_event(self, event_id):
        """Get a ScalarEvent object from the ASDF file.

        Args:
            event_id (str):
                ID of event to search for in ASDF file.

        Returns:
            ScalarEvent:
                Flattened version of Obspy Event object.
        """
        obspy_event = None
        for event in self.dataset.events:
            if event.resource_id.id.find(event_id) > -1:
                obspy_event = event
                break
        scalar_event = ScalarEvent.from_obspy(obspy_event) if obspy_event else None
        return scalar_event

    def get_provenance(self, event_id, stations=None, labels=None):
        """Return DataFrame with processing history matching input criteria.

                Output will look like this:
                Record  Processing Step     Step Attribute              Attribute Value
        0  NZ.HSES.HN1  Remove Response        input_units                       counts
        1  NZ.HSES.HN1  Remove Response       output_units                       cm/s^2
        2  NZ.HSES.HN1          Detrend  detrending_method                       linear
        3  NZ.HSES.HN1          Detrend  detrending_method                       demean
        4  NZ.HSES.HN1              Cut       new_end_time  2016-11-13T11:05:44.000000Z
        5  NZ.HSES.HN1              Cut     new_start_time  2016-11-13T11:02:58.000000Z
        6  NZ.HSES.HN1            Taper               side                         both
        7  NZ.HSES.HN1            Taper        taper_width                         0.05
        8  NZ.HSES.HN1            Taper        window_type                         Hann
        ...

                Args:
                    event_id (str):
                        Event ID corresponding to an Event in the workspace.
                    stations (list):
                        List of stations to search for.
                    labels (list):
                        List of processing labels to search for.

                Returns:
                    DataFrame:
                        Table of processing steps/parameters (see above).

        """
        if stations is None:
            stations = self.get_stations()
        if labels is None:
            labels = self.get_labels()
        cols = ["Record", "Processing Step", "Step Attribute", "Attribute Value"]
        df_dicts = []
        for provname in self.dataset.provenance.list():
            has_station = False
            for station in stations:
                if station in provname:
                    has_station = True
                    break
            has_label = False
            for label in labels:
                if label in provname:
                    has_label = True
                    break
            if not has_label or not has_station:
                continue

            provdoc = self.dataset.provenance[provname]
            serial = json.loads(provdoc.serialize())
            for _, attrs in serial["activity"].items():
                pstep = None
                for key, value in attrs.items():
                    if key == "prov:label":
                        pstep = value
                        continue
                    if key == "prov:type":
                        continue
                    if not isinstance(value, str):
                        if value["type"] == "xsd:dateTime":
                            value = UTCDateTime(value["$"])
                        elif value["type"] == "xsd:double":
                            value = float(value["$"])
                        elif value["type"] == "xsd:int":
                            value = int(value["$"])
                        else:
                            pass
                    attrkey = key.replace("seis_prov:", "")
                    row = pd.Series(index=cols, dtype=object)
                    row["Record"] = provname
                    row["Processing Step"] = pstep
                    row["Step Attribute"] = attrkey
                    row["Attribute Value"] = value
                    df_dicts.append(row)

        df = pd.DataFrame.from_dict(df_dicts)
        df = df[cols]

        return df

    @staticmethod
    def _get_id(event):
        eid = event.origins[0].resource_id.id.replace("smi:local/", "")
        return eid

    @staticmethod
    def _get_agents(provdoc):
        software = {}
        person = {}
        jdict = json.loads(provdoc.serialize())
        for key, value in jdict["agent"].items():
            is_person = re.search("sp[0-9]{3}_pp", key) is not None
            is_software = re.search("sp[0-9]{3}_sa", key) is not None
            if is_person:
                person["id"] = value["prov:label"]
                if "seis_prov:email" in value:
                    person["email"] = value["seis_prov:email"]
                if "seis_prov:name" in value:
                    person["name"] = value["seis_prov:name"]
            elif is_software:
                software["name"] = value["seis_prov:software_name"]
                software["version"] = value["seis_prov:software_version"]
            else:
                pass

        if "name" not in person:
            person["name"] = ""
        if "email" not in person:
            person["email"] = ""
        return (person, software)


def dict_to_str(indict):
    def _serializer(value):
        if isinstance(value, UTCDateTime):
            return value.strftime(TIMEFMT_MS)
        if hasattr(value, "__dict__"):
            return value.__dict__
        if isinstance(value, bytes):
            return value.decode()
        raise ValueError(f"Could not serialize {value} of type {type(value)}.")

    return json.dumps(indict, default=_serializer)


def str_to_array(value):
    return np.frombuffer(value.encode("utf-8"), dtype=np.uint8)


def array_to_str(data):
    str_buffer = io.BytesIO(data[:])
    return str_buffer.read().decode()


def camel_case_split(identifier):
    matches = re.finditer(
        ".+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)", identifier
    )
    return [m.group(0) for m in matches]
