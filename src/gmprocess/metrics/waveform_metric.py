"""Module for the WaveformMetric class."""

from abc import ABC, abstractmethod

from gmprocess.utils import constants


class WaveformMetric(ABC):
    """Base class for waveform metric classes."""

    def __repr__(self):
        comps = ", ".join({f"{k}={v:.3f}" for (k, v) in self._values.items()})
        return f"{self.identifier}: {comps}"

    def __init__(self):
        self._values = None
        self._type = None
        self.format_type = None
        self._units = None
        self.metric_attributes = None
        self.component_to_channel = None

    def to_dict(self):
        """Return a dictionary representation of the Metric object."""
        return {
            "values": list(self._values.values()),
            "components": self.components,
            "type": self._type,
            "format_type": self.format_type,
            "units": self._units,
            "metric_attributes": self.metric_attributes,
            "component_to_channel": self.component_to_channel,
        }

    @property
    def type(self):
        """Type is the metric type and does not include metric attributes.

        Note that this is the simplest name and we define it to be identical to the
        name of the Metric subclass.
        """
        return self._type

    @property
    @abstractmethod
    def identifier(self):
        """The identifier includes metric attributes, but not values/components."""

    @property
    def values(self):
        """Values is a dictionary with keys for components."""
        return self._values

    @property
    def units(self):
        """String representation of metric units."""
        return self._units

    @property
    def components(self):
        """The available components."""
        return list(self._values.keys())

    def value(self, component):
        """Return the value for the specified component"""
        return self._values[component]

    @staticmethod
    def metric_from_dict(mdict):
        """Class factory to create a Metric subclass instance from a dictionary.

        Args:
            mdict (dict):
                A dictionary with the structure of the dictionary that is returned by
                Metric.to_dict().
        """
        # List of subclasses
        metric_subclasses = WaveformMetric.__subclasses__()

        # Dictionary for selecting a subclass
        sub_dict = {m.__name__: m for m in metric_subclasses}

        # Name of subclass is in the "type" key
        selected_class = sub_dict[mdict["type"]]

        # Prepare the arguments to construct a class instance
        cargs = mdict.copy()
        rm_keys = ["type", "format_type", "units"]
        for k in rm_keys:
            cargs.pop(k)
        attr = cargs.pop("metric_attributes")
        for k, v in attr.items():
            cargs[k] = v
        return selected_class(**cargs)


class PGA(WaveformMetric):
    """WaveformMetric subclass for PGA."""

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
        super().__init__()
        if len(values) != len(components):
            raise ValueError("Length of values must equal length of components.")

        self._values = dict(zip(components, values))
        self._type = self.__class__.__name__
        self.format_type = "pgm"
        self._units = constants.UNITS[self._type.lower()]
        self.metric_attributes = {}
        self.component_to_channel = component_to_channel

    @property
    def identifier(self):
        return "PGA"


class PGV(WaveformMetric):
    """WaveformMetric subclass for PGV."""

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
        super().__init__()
        if len(values) != len(components):
            raise ValueError("Length of values must equal length of components.")

        self._values = dict(zip(components, values))
        self._type = self.__class__.__name__
        self.format_type = "pgm"
        self._units = constants.UNITS[self._type.lower()]
        self.metric_attributes = {}
        self.component_to_channel = component_to_channel

    @property
    def identifier(self):
        return "PGV"


class SA(WaveformMetric):
    """WaveformMetric subclass for SA, spectral acceleration."""

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
        super().__init__()
        if len(values) != len(components):
            raise ValueError("Length of values must equal length of components.")

        self._values = dict(zip(components, values))
        self._type = self.__class__.__name__
        self.format_type = "pgm"
        self._units = constants.UNITS[self._type.lower()]
        self.metric_attributes = {
            "period": period,
            "damping": damping,
        }
        self.component_to_channel = component_to_channel

    @property
    def identifier(self):
        attrs = self.metric_attributes
        return f"SA(T={float(attrs['period']):.4f}, D={float(attrs['damping']):.3f})"


class FAS(WaveformMetric):
    """WaveformMetric subclass for FAS, Fourier amplitude spectra."""

    def __init__(
        self,
        values,
        components,
        period,
        smoothing=20.0,
        method="Konno-Omachi",
        component_to_channel=None,
    ):
        """Construct a FAS metric object.

        Args:
            values (list):
                List of FAS values.
            components (list):
                List of the components that map to the FAS values.
            period (float):
                Period for this fAS (in seconds).
            smoothing (float):
                Smoothing bandwidth parameter; default is 20.
            method (str):
                Smoothing method; default is Konno-Omachi.
            component_to_channel (dict):
                Optional dictionary mapping the simplifued component names to the
                as-recorded channel names.
        """
        super().__init__()
        if len(values) != len(components):
            raise ValueError("Length of values must equal length of components.")

        self._values = dict(zip(components, values))
        self._type = self.__class__.__name__
        self.format_type = "pgm"
        self._units = constants.UNITS[self._type.lower()]
        self.metric_attributes = {
            "period": period,
            "smoothing": smoothing,
            "method": method,
        }
        self.component_to_channel = component_to_channel

    @property
    def identifier(self):
        attrs = self.metric_attributes
        return f"FAS(T={float(attrs['period']):.4f}, B={float(attrs['smoothing']):.1f})"


class Duration(WaveformMetric):
    """WaveformMetric subclass for duration."""

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
        super().__init__()
        if len(values) != len(components):
            raise ValueError("Length of values must equal length of components.")

        self._values = dict(zip(components, values))
        self._type = self.__class__.__name__
        self.format_type = "pgm"
        self._units = constants.UNITS[self._type.lower()]
        self.metric_attributes = {
            "interval": interval,
        }
        self.component_to_channel = component_to_channel

    @property
    def identifier(self):
        attrs = self.metric_attributes
        return f"Duration({attrs['interval']})"


class SortedDuration(WaveformMetric):
    """WaveformMetric subclass for sorted duration."""

    def __init__(self, values, components, component_to_channel=None):
        """Construct a SortedDuration metric object.

        Args:
            values (list):
                List of Sorted Duration values.
            components (list):
                List of the components that map to the Sorted Duration values.
            component_to_channel (dict):
                Optional dictionary mapping the simplifued component names to the
                as-recorded channel names.
        """
        super().__init__()
        if len(values) != len(components):
            raise ValueError("Length of values must equal length of components.")

        self._values = dict(zip(components, values))
        self._type = self.__class__.__name__
        self.format_type = "pgm"
        self._units = constants.UNITS[self._type.lower()]
        self.metric_attributes = {}
        self.component_to_channel = component_to_channel

    @property
    def identifier(self):
        return "SortedDuration"


class AriasIntensity(WaveformMetric):
    """WaveformMetric subclass for Arias Intensity."""

    def __init__(self, values, components, component_to_channel=None):
        """Construct a AriasIntensity metric object.

        Args:
            values (list):
                List of Arias Intensity values.
            components (list):
                List of the components that map to the Arias Intensity values.
            component_to_channel (dict):
                Optional dictionary mapping the simplifued component names to the
                as-recorded channel names.
        """
        super().__init__()
        if len(values) != len(components):
            raise ValueError("Length of values must equal length of components.")

        self._values = dict(zip(components, values))
        self._type = self.__class__.__name__
        self.format_type = "pgm"
        self._units = constants.UNITS[self._type.lower()]
        self.metric_attributes = {}
        self.component_to_channel = component_to_channel

    @property
    def identifier(self):
        return "AriasIntensity"
