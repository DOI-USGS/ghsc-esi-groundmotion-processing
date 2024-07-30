"""Module for handling provenance documents.

From SEIS-PROV docs regarding IDs:
- Examples: sp027_bs_ea78b46, sp001_wf_f84fb9a
- Three parts, split by underscore:
    1) Always includes "sp" and a 3 digit zero-padded integer that indicates the
        step.
    2) Two letter code indicating the type of entity or activity
        (maps to Provenance.ACTIVITIES["code"]) below.
    3) A 7 to 12 letter lowercase alphanumeric hash to ensure uniqueness of ids.

Note that it is important to recognize the difference between the above ID and the
"prov:id" provenance property, which corresponds to the keys in Provenance.ACTIVITIES.
"""

from abc import ABC, abstractmethod
import logging
from datetime import datetime
import getpass
import json

import pandas as pd
from obspy.core.utcdatetime import UTCDateTime

import prov
import prov.model

from gmprocess.utils.config import get_config


class Provenance(ABC):
    """Parent class for Provenance classes."""

    NS_PREFIX = "seis_prov"
    NS_SEIS = (NS_PREFIX, "http://seisprov.org/seis_prov/0.1/#")
    MAX_ID_LEN = 12
    PROV_TIME_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"
    TIMEFMT = "%Y-%m-%dT%H:%M:%SZ"

    def __init__(self):
        # list of provenance activity entries (dictionaries).
        self.provenance_list = []

    def _new_provenance_document(self):
        self.provenance_document = prov.model.ProvDocument()
        self.provenance_document.add_namespace(*self.NS_SEIS)

    def _from_provenance_document(self, provdoc):
        json_prov = json.loads(provdoc.serialize())
        for prov_type, prov_entry in json_prov.items():
            if prov_type != "activity":
                continue
            for _, prov_properties in prov_entry.items():
                # key in this loop is the full SEIS-PROV ID like sp001_wf_f84fb9a,
                # not to be confused with the "prov:id" property, which is what we
                # use (and is more human-readable).
                prov_attributes = {}
                for property_name, property_value in prov_properties.items():
                    if property_name == "prov:label":
                        continue
                    elif property_name == "prov:type":
                        prov_id = self._prov_id_from_property_value(property_value)
                    else:
                        attribute_name = property_name.split(":")[1]
                        if isinstance(property_value, dict):
                            property_value = property_value["$"]
                        elif isinstance(property_value, datetime):
                            property_value = UTCDateTime(property_value)
                        prov_attributes[attribute_name] = property_value
                if prov_attributes:
                    self.append(
                        {"prov_id": prov_id, "prov_attributes": prov_attributes}
                    )

    @abstractmethod
    def append(self, prov_dict):
        pass

    @staticmethod
    @abstractmethod
    def _prov_id_from_property_value(property_value):
        pass


class LabelProvenance(Provenance):
    """Class for dealing with label-level provenance."""

    def __init__(self, label, gmprocess_version="unknown", config=None):
        """Initialize LabelProvenance class.

        Args:
            label (str):
                Processing label.
            gmprocess_version (str):
                gmprocess version.
            config (dict):
                Configuration options.
        """
        super().__init__()
        self.label = label
        self._new_provenance_document()
        self._set_person_agent(config)
        self._set_software_agent(gmprocess_version)

    def __repr__(self):
        prov_str = f"Provenance for label '{self.label}' includes:\n"
        jdict = json.loads(self.provenance_document.serialize())
        for _, adict in jdict["agent"].items():
            prov_str += f"- {adict['prov:type']['$']}, {adict['prov:label']}\n"
        return prov_str

    def append(self, prov_dict):
        """Append a provenance entry.

        Args:
            prov_dict (dict):
                Dictionary with keys "prov_id" and "prov_attributes".
        """
        self.provenance_list.append(prov_dict)

    @classmethod
    def from_provenance_document(cls, provdoc, label, config):
        """Add provenance entires from a provenance document.

        Args:
            provdoc (prov.model.ProvDocument):
                Provenance document.
            label (str):
                Processing label.
            config (dict):
                Dictionary of config options.
        """
        prov_obj = cls(label, config=config)
        prov_obj._from_provenance_document(provdoc)
        return prov_obj

    @staticmethod
    def _prov_id_from_property_value(property_value):
        if isinstance(property_value, dict):
            return property_value["$"].split(":")[1]
        else:
            return property_value.split(":")[1]

    def to_provenance_document(self):
        """Return the contents as a provenance document."""
        return self.provenance_document

    def _set_software_agent(self, gmprocess_version):
        """Get the seis-prov entity for the gmprocess software.

        Args:
            gmprocess_version (str):
                gmprocess version.

        Returns:
            prov.model.ProvDocument:
                Provenance document updated with gmprocess software name/version.
        """
        software = "gmprocess"
        hashstr = "0000001"
        agent_id = f"seis_prov:sp001_sa_{hashstr}"
        giturl = "https://code.usgs.gov/ghsc/esi/groundmotion-processing"
        self.provenance_document.agent(
            agent_id,
            other_attributes=(
                (
                    ("prov:label", software),
                    (
                        "prov:type",
                        prov.identifier.QualifiedName(
                            prov.constants.PROV, "SoftwareAgent"
                        ),
                    ),
                    ("seis_prov:software_name", software),
                    ("seis_prov:software_version", gmprocess_version),
                    (
                        "seis_prov:website",
                        prov.model.Literal(giturl, prov.constants.XSD_ANYURI),
                    ),
                )
            ),
        )

    def _set_person_agent(self, config=None):
        """Get the seis-prov entity for the user software.

        Args:
            config (dict):
                Configuration options.

        Returns:
            prov.model.ProvDocument:
                Provenance document updated with gmprocess software name/version.
        """
        username = getpass.getuser()
        if config is None:
            config = get_config()
        fullname = ""
        email = ""
        if "user" in config:
            if "name" in config["user"]:
                fullname = config["user"]["name"]
            if "email" in config["user"]:
                email = config["user"]["email"]
        hashstr = "0000001"
        person_id = f"seis_prov:sp001_pp_{hashstr}"
        self.provenance_document.agent(
            person_id,
            other_attributes=(
                (
                    ("prov:label", username),
                    (
                        "prov:type",
                        prov.identifier.QualifiedName(prov.constants.PROV, "Person"),
                    ),
                    ("seis_prov:name", fullname),
                    ("seis_prov:email", email),
                )
            ),
        )


class TraceProvenance(Provenance):
    """Class for dealing with trace-level provenance."""

    ACTIVITIES = {
        "waveform_simulation": {"code": "ws", "label": "Waveform Simulation"},
        "taper": {"code": "tp", "label": "Taper"},
        "stack_cross_correlations": {"code": "sc", "label": "Stack Cross Correlations"},
        "simulate_response": {"code": "sr", "label": "Simulate Response"},
        "rotate": {"code": "rt", "label": "Rotate"},
        "resample": {"code": "rs", "label": "Resample"},
        "remove_response": {"code": "rr", "label": "Remove Response"},
        "pad": {"code": "pd", "label": "Pad"},
        "normalize": {"code": "nm", "label": "Normalize"},
        "multiply": {"code": "nm", "label": "Multiply"},
        "merge": {"code": "mg", "label": "Merge"},
        "lowpass_filter": {"code": "lp", "label": "Lowpass Filter"},
        "interpolate": {"code": "ip", "label": "Interpolate"},
        "integrate": {"code": "ig", "label": "Integrate"},
        "highpass_filter": {"code": "hp", "label": "Highpass Filter"},
        "divide": {"code": "dv", "label": "Divide"},
        "differentiate": {"code": "df", "label": "Differentiate"},
        "detrend": {"code": "dt", "label": "Detrend"},
        "decimate": {"code": "dc", "label": "Decimate"},
        "cut": {"code": "ct", "label": "Cut"},
        "cross_correlate": {"code": "co", "label": "Cross Correlate"},
        "calculate_adjoint_source": {"code": "ca", "label": "Calculate Adjoint Source"},
        "bandstop_filter": {"code": "bs", "label": "Bandstop Filter"},
        "bandpass_filter": {"code": "bp", "label": "Bandpass Filter"},
    }

    def __init__(self, stats):
        """Initialize TraceProvenance class.

        Args:
            stats:
                A Trace stats object.
        """
        super().__init__()
        self.stats = stats

    def __repr__(self):
        fmt = "%s.%s.%s.%s"
        tpl = (
            self.stats.network,
            self.stats.station,
            self.stats.channel,
            self.stats.location,
        )
        nscl = fmt % tpl
        prov_str = f"Provenance for Trace '{nscl}' includes:\n"
        for prov_dict in self:
            prov_str += f"- {prov_dict['prov_id']}\n"
        return prov_str

    def to_provenance_document(self):
        """Return the contents as a provenance document."""
        self._new_provenance_document()
        sequence = 1
        for provdict in self:
            provid = provdict["prov_id"]
            prov_attributes = provdict["prov_attributes"]
            if provid not in self.ACTIVITIES:
                fmt = "Unknown or invalid processing parameter %s"
                logging.info(fmt, provid)
                continue
            self._set_activity(provid, prov_attributes, sequence)
            sequence += 1
        return self.provenance_document

    def __iter__(self):
        """Provenance iterator."""
        return self.provenance_list.__iter__()

    @property
    def ids(self):
        """Return a list of all prov IDs."""
        id_list = []
        for provdict in self:
            id_list.append(provdict["prov_id"])
        return id_list

    def append(self, prov_dict):
        """Append a provenance entry.

        Args:
            prov_dict (dict):
                Dictionary with keys "prov_id" and "prov_attributes".
        """
        if prov_dict["prov_id"] not in self.ACTIVITIES:
            raise ValueError(
                f"Unknown or invalid processing parameter {prov_dict['prov_id']}."
            )
        self.provenance_list.append(prov_dict)

    def select(self, prov_id):
        """Return only the provenance entries that match a given prov_id.

        Args:
            prov_id (str):
                The string to match for the provenance id.
        """
        matching_prov = []
        for provdict in self:
            if provdict["prov_id"] == prov_id:
                matching_prov.append(provdict)
        return matching_prov

    @classmethod
    def from_provenance_document(cls, provdoc, stats):
        """Add provenance entries from a provenance document.

        Args:
            provdoc (prov.model.ProvDocument):
                Provenance document.
            stats:
                StationTrace stats object.
        """
        prov_obj = cls(stats)
        prov_obj._from_provenance_document(provdoc)
        return prov_obj

    @staticmethod
    def _prov_id_from_property_value(property_value):
        return property_value.split(":")[1]

    def _set_activity(self, activity, attributes, sequence):
        """Get the seis-prov entity for an input processing "activity".

        See
        http://seismicdata.github.io/SEIS-PROV/_generated_details.html#activities

        for details on the types of activities that are possible to capture.


        Args:
            activity (str):
                The prov:id for the input activity.
            attributes (dict):
                The attributes associated with the activity.
            sequence (int):
                Integer used to identify the order in which the activities were
                performed.
        """
        activity_dict = self.ACTIVITIES[activity]
        hashid = "%07i" % sequence
        code = activity_dict["code"]
        label = activity_dict["label"]
        activity_id = "sp%03i_%s_%s" % (sequence, code, hashid)
        pr_attributes = [("prov:label", label), ("prov:type", f"seis_prov:{activity}")]
        for key, value in attributes.items():
            if isinstance(value, float):
                value = prov.model.Literal(value, prov.constants.XSD_DOUBLE)
            elif isinstance(value, int):
                value = prov.model.Literal(value, prov.constants.XSD_INT)
            elif isinstance(value, UTCDateTime):
                value = prov.model.Literal(
                    value.strftime(self.TIMEFMT), prov.constants.XSD_DATETIME
                )

            att_tuple = (f"seis_prov:{key}", value)
            pr_attributes.append(att_tuple)
        self.provenance_document.activity(
            f"seis_prov:{activity_id}", other_attributes=pr_attributes
        )

    def get_prov_dataframe(self):
        """Generate a pandas data frame summary of the provenance."""
        columns = ["Process Step", "Process Attribute", "Process Value"]
        df = pd.DataFrame(columns=columns)
        values = []
        attributes = []
        steps = []
        indices = []
        index = 0
        for provdict in self:
            provid = provdict["prov_id"]
            provstep = self.ACTIVITIES[provid]["label"]
            prov_attrs = provdict["prov_attributes"]
            steps += [provstep] * len(prov_attrs)
            indices += [index] * len(prov_attrs)
            for key, value in prov_attrs.items():
                attributes.append(key)
                if isinstance(value, UTCDateTime):
                    value = value.datetime.strftime("%Y-%m-%d %H:%M:%S")
                values.append(str(value))
            index += 1

        mdict = {
            "Index": indices,
            "Process Step": steps,
            "Process Attribute": attributes,
            "Process Value": values,
        }
        df = pd.DataFrame(mdict)
        return df

    def get_prov_series(self):
        """Return a pandas Series containing the processing history for the
        trace.

        BO.NGNH31.HN2   Remove Response   input_units   counts
        -                                 output_units  cm/s^2
        -               Taper             side          both
        -                                 window_type   Hann
        -                                 taper_width   0.05

        Returns:
            Series:
                Pandas Series (see above).
        """
        tpl = (self.stats.network, self.stats.station, self.stats.channel)
        recstr = "%s.%s.%s" % tpl
        values = []
        attributes = []
        steps = []
        for provdict in self:
            provid = provdict["prov_id"]
            provstep = self.ACTIVITIES[provid]["label"]
            prov_attrs = provdict["prov_attributes"]
            steps += [provstep] * len(prov_attrs)
            for key, value in prov_attrs.items():
                attributes.append(key)
                values.append(str(value))
        records = [recstr] * len(attributes)
        index = [records, steps, attributes]
        row = pd.Series(values, index=index)
        return row
