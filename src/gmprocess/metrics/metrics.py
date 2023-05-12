#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod

from lxml import etree

from gmprocess.utils import constants

DEFAULT_DAMPING = 0.05


class Metric(ABC):
    @property
    @abstractmethod
    def units(self):
        pass

    @property
    @abstractmethod
    def values(self):
        pass

    @property
    @abstractmethod
    def type(self):
        pass

    def to_xml(self):
        root = etree.Element("waveform_metrics")
        imtstr = self.type.lower()
        units = self.units
        attrs = self.metric_attributes

        fmt = constants.METRICS_XML_FLOAT_STRING_FORMAT

        attdict = {"units": units}

        for att, atval in attrs.items():
            if isinstance(atval, str):
                attdict[att] = atval
            else:
                attdict[att] = fmt[att] % atval

        imt_tag = etree.SubElement(root, imtstr, attrib=attdict)

        for imc in self.components:
            imcstr = imc.lower().replace("(", "").replace(")", "")
            if self.component_to_channel and imc in self.component_to_channel:
                attributes = {"original_channel": self.component_to_channel[imc]}
            else:
                attributes = {}
            imc_tag = etree.SubElement(imt_tag, imcstr, attrib=attributes)
            imc_tag.text = fmt[self._format_type] % self.value(imc)
        return etree.tostring(root, encoding="unicode")


class PGA(Metric):
    def __init__(self, values, components, component_to_channel=None):
        """Construct a PGA metric object.

        Args:
            values (list):
                List of PGA values.
            components (list):
                List of the components that map to the PGA values.
            component_to_channel (dict):
                Optional dictionary mapping the simplifued component names to the
                as-recorded channel names.
        """
        if len(values) != len(components):
            raise ValueError("Length of values must equal length of components.")

        self._values = dict(zip(components, values))
        self._type = "PGA"
        self._format_type = "pgm"
        self._units = constants.UNITS[self._type.lower()]
        self.metric_attributes = {}
        self.component_to_channel = component_to_channel

    @property
    def values(self):
        return self._values

    @property
    def units(self):
        return self._units

    @property
    def type(self):
        return self._type

    @property
    def components(self):
        return self._values.keys()

    def value(self, component):
        """Return the value for the specified component"""
        return self._values[component]

    def __repr__(self):
        return "PGA"


class PGV(Metric):
    def __init__(self, values, components, component_to_channel=None):
        """Construct a PGV metric object.

        Args:
            values (list):
                List of PGV values.
            components (list):
                List of the components that map to the PGV values.
            component_to_channel (dict):
                Optional dictionary mapping the simplifued component names to the
                as-recorded channel names.
        """
        if len(values) != len(components):
            raise ValueError("Length of values must equal length of components.")

        self._values = dict(zip(components, values))
        self._type = "PGV"
        self._format_type = "pgm"
        self._units = constants.UNITS[self._type.lower()]
        self.metric_attributes = {}
        self.component_to_channel = component_to_channel

    @property
    def values(self):
        return self._values

    @property
    def units(self):
        return self._units

    @property
    def type(self):
        return self._type

    @property
    def components(self):
        return self._values.keys()

    def value(self, component):
        """Return the value for the specified component"""
        return self._values[component]

    def __repr__(self):
        return "PGV"


class SA(Metric):
    def __init__(
        self, values, components, period, damping=5.0, component_to_channel=None
    ):
        """Construct a SA metric object.

        Args:
            values (list):
                List of SA values.
            components (list):
                List of the components that map to the SA values.
            period (float):
                Oscillator period for this SA (in seconds).
            damping (float):
                Percentage of critical damping.
            component_to_channel (dict):
                Optional dictionary mapping the simplifued component names to the
                as-recorded channel names.
        """
        if len(values) != len(components):
            raise ValueError("Length of values must equal length of components.")

        self._values = dict(zip(components, values))
        self._type = "SA"
        self._format_type = "pgm"
        self._units = constants.UNITS[self._type.lower()]
        self.metric_attributes = {
            "period": period,
            "damping": damping,
        }
        self.component_to_channel = component_to_channel

    @property
    def values(self):
        return self._values

    @property
    def units(self):
        return self._units

    @property
    def type(self):
        return self._type

    @property
    def components(self):
        return self._values.keys()

    def value(self, component):
        """Return the value for the specified component"""
        return self._values[component]

    def __repr__(self):
        attrs = self.metric_attributes
        return f"SA(T={attrs['period']:.4f}, D={attrs['damping']:.3f})"


class Duration(Metric):
    def __init__(self, values, components, interval, component_to_channel=None):
        """Construct a Duration metric object.

        Args:
            values (list):
                List of Duration values.
            components (list):
                List of the components that map to the Duration values.
            interval (str):
                Significant duration interval in percentage of Arias Intensity in which
                the start and end percentages are separated by a hyphen: e.g., "5-75".
            component_to_channel (dict):
                Optional dictionary mapping the simplifued component names to the
                as-recorded channel names.
        """
        if len(values) != len(components):
            raise ValueError("Length of values must equal length of components.")

        self._values = dict(zip(components, values))
        self._type = "Duration"
        self._format_type = "duration"
        self._units = constants.UNITS[self._type.lower()]
        self.metric_attributes = {
            "interval": interval,
        }
        self.component_to_channel = component_to_channel

    @property
    def values(self):
        return self._values

    @property
    def units(self):
        return self._units

    @property
    def type(self):
        return self._type

    @property
    def components(self):
        return self._values.keys()

    def value(self, component):
        """Return the value for the specified component"""
        return self._values[component]

    def __repr__(self):
        attrs = self.metric_attributes
        return f"Duration({attrs['interval']})"
