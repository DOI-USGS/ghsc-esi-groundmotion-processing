"""Module for WaveformMetricType classes."""

from abc import ABC, abstractmethod

from gmprocess.utils import constants


class WaveformMetricType(ABC):
    """Base class for waveform metric classes."""

    def __init__(self):
        self._values = None
        self._type = None
        self.format_type = None
        self._units = None
        self.metric_attributes = None
        self.component_to_channel = None

    def to_dict(self):
        """Return a dictionary representation of the WaveformMetricType object."""
        return {
            "values": list(self._values.values()),
            "components": self.components,
            "type": self._type,
            "format_type": self.format_type,
            "units": self._units,
            "metric_attributes": self.metric_attributes,
            "component_to_channel": self.component_to_channel,
        }

    def __repr__(self):
        comps = ", ".join({f"{k}={v:.3f}" for (k, v) in self._values.items()})
        return f"{self.identifier}: {comps}"

    @property
    def type(self):
        """Type is the metric type and does not include metric attributes.

        Note that this is the simplest name and we define it to be identical to the
        name of the WaveformMetricType subclass.
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
        """Return the value for the specified component.

        Args:
            component (str):
                String representaiton of a WaveformMetricComponent.
        """
        for k, v in self._values.items():
            if str(k) == str(component):
                return v

    @staticmethod
    def metric_from_dict(mdict):
        """Class factory to create a WaveformMetricType from a dictionary.

        Args:
            mdict (dict):
                A dictionary with the structure of the dictionary that is returned by
                WaveformMetricType.to_dict().
        """
        # List of subclasses
        metric_subclasses = WaveformMetricType.__subclasses__()

        # Dictionary for selecting a subclass
        sub_dict = {m.__name__.lower(): m for m in metric_subclasses}

        # Name of subclass is in the "type" key
        selected_class = sub_dict[mdict["type"].lower()]

        # Prepare the arguments to construct a class instance
        cargs = mdict.copy()
        rm_keys = ["type", "format_type", "units"]
        for k in rm_keys:
            cargs.pop(k)
        attr = cargs.pop("metric_attributes")
        for k, v in attr.items():
            cargs[k] = v
        return selected_class(**cargs)


class PGA(WaveformMetricType):
    """WaveformMetricType subclass for PGA."""

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


class PGV(WaveformMetricType):
    """WaveformMetricType subclass for PGV."""

    def __init__(self, values, components, component_to_channel=None, **kwargs):
        """Construct a PGV metric object.

        Note: kwargs is needed because there are parameters that will get automatically
        passed here due to the integration processing step that we do not actually
        want to keep as metric parameters.

        Args:
            values (list):
                List of PGV values.
            components (list):
                List of the components that map to the PGV values.
            component_to_channel (dict):
                Optional dictionary mapping the simplified component names to the
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


class SA(WaveformMetricType):
    """WaveformMetricType subclass for SA, spectral acceleration."""

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
                Optional dictionary mapping the simplified component names to the
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


class PSA(WaveformMetricType):
    """WaveformMetricType subclass for PSA, pseudo-spectral acceleration."""

    def __init__(
        self, values, components, period, damping=5.0, component_to_channel=None
    ):
        """Construct a PSA metric object.

        Args:
            values (list):
                List of PSA values.
            components (list):
                List of the components that map to the PSA values.
            period (float):
                Oscillator period for this PSA (in seconds).
            damping (float):
                Percentage of critical damping.
            component_to_channel (dict):
                Optional dictionary mapping the simplified component names to the
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
        return f"PSA(T={float(attrs['period']):.4f}, D={float(attrs['damping']):.3f})"


class SV(WaveformMetricType):
    """WaveformMetricType subclass for SV, spectral velocity."""

    def __init__(
        self, values, components, period, damping=5.0, component_to_channel=None
    ):
        """Construct a SV metric object.

        Args:
            values (list):
                List of SV values.
            components (list):
                List of the components that map to the SV values.
            period (float):
                Oscillator period for this SV (in seconds).
            damping (float):
                Percentage of critical damping.
            component_to_channel (dict):
                Optional dictionary mapping the simplified component names to the
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
        return f"SV(T={float(attrs['period']):.4f}, D={float(attrs['damping']):.3f})"


class PSV(WaveformMetricType):
    """WaveformMetricType subclass for PSV, pseudo-spectral velocity."""

    def __init__(
        self, values, components, period, damping=5.0, component_to_channel=None
    ):
        """Construct a PSV metric object.

        Args:
            values (list):
                List of PSV values.
            components (list):
                List of the components that map to the PSV values.
            period (float):
                Oscillator period for this PSV (in seconds).
            damping (float):
                Percentage of critical damping.
            component_to_channel (dict):
                Optional dictionary mapping the simplified component names to the
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
        return f"PSV(T={float(attrs['period']):.4f}, D={float(attrs['damping']):.3f})"


class SD(WaveformMetricType):
    """WaveformMetricType subclass for SD, spectral displacement."""

    def __init__(
        self, values, components, period, damping=5.0, component_to_channel=None
    ):
        """Construct a SD metric object.

        Args:
            values (list):
                List of SD values.
            components (list):
                List of the components that map to the SA values.
            period (float):
                Oscillator period for this SA (in seconds).
            damping (float):
                Percentage of critical damping.
            component_to_channel (dict):
                Optional dictionary mapping the simplified component names to the
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
        return f"SD(T={float(attrs['period']):.4f}, D={float(attrs['damping']):.3f})"


class FAS(WaveformMetricType):
    """WaveformMetricType subclass for FAS, Fourier amplitude spectra."""

    def __init__(
        self,
        values,
        components,
        frequencies,  # noqa
        smoothing_parameter=20.0,
        smoothing_method="Konno-Omachi",
        allow_nans=True,
        component_to_channel=None,
    ):
        """Construct a FAS metric object.

        Note that "frequencies" is passed in as a metric parameter, but the resulting
        array of frequencies is in the "values" container so there's no need to do
        anything with the "frequencies" array.

        Args:
            values (list):
                List of FAS values.
            components (list):
                List of the components that map to the FAS values.
            frequencies (array):
                Frequencies for this FAS (Hz).
            smoothing_parameter (float):
                Smoothing bandwidth parameter; default is 20.
            smoothing_method (str):
                Smoothing method; default is Konno-Omachi.
            allow_nans (book):
                Default (True) just uses the number of points in the record, which can
                result in nans when smoothed using the Konno-Omachi method. False
                adjusts the number of points in the FFT to ensure no nans.
            component_to_channel (dict):
                Optional dictionary mapping the simplified component names to the
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
            "smoothing_parameter": smoothing_parameter,
            "smoothing_method": smoothing_method,
            "allow_nans": allow_nans,
        }
        self.component_to_channel = component_to_channel

    @property
    def identifier(self):
        attrs = self.metric_attributes
        return f"FAS(B={float(attrs['smoothing_parameter']):.1f})"

    def __repr__(self):
        return f"{self.identifier}: {self.components}"


class Duration(WaveformMetricType):
    """WaveformMetricType subclass for duration."""

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
                Optional dictionary mapping the simplified component names to the
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


class SortedDuration(WaveformMetricType):
    """WaveformMetricType subclass for sorted duration."""

    def __init__(self, values, components, component_to_channel=None):
        """Construct a SortedDuration metric object.

        Args:
            values (list):
                List of Sorted Duration values.
            components (list):
                List of the components that map to the Sorted Duration values.
            component_to_channel (dict):
                Optional dictionary mapping the simplified component names to the
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


class Arias(WaveformMetricType):
    """WaveformMetricType subclass for Arias Intensity."""

    def __init__(self, values, components, component_to_channel=None):
        """Construct a Arias metric object.

        Args:
            values (list):
                List of Arias Intensity values.
            components (list):
                List of the components that map to the Arias Intensity values.
            component_to_channel (dict):
                Optional dictionary mapping the simplified component names to the
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
        return "Arias"


class CAV(WaveformMetricType):
    """WaveformMetricType subclass for Cumulative Absolute Velocity."""

    def __init__(self, values, components, component_to_channel=None):
        """Construct a CAV metric object.

        Args:
            values (list):
                List of Cumulative Absolute Velocity values.
            components (list):
                List of the components that map to the Cumulative Absolute Velocity
                values.
            component_to_channel (dict):
                Optional dictionary mapping the simplified component names to the
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
        return "CAV"
