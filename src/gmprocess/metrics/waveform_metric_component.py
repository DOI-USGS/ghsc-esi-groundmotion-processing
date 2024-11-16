"""Module for the WaveformMetricComponent class."""

from abc import ABC


def get_supported_metric_types(wmc_string):
    """Helper function to get supported_metric_types from string representation.

    Args:
        wmc_string (str):
            String representation of the WaveformMetricComponent, e.g.,
            "RotD(percentile=50.0)".
    """
    if wmc_string.startswith("Channels"):
        smt = Channels(channel="", component_string="").supported_metric_types
    elif wmc_string.startswith("ArithmeticMean"):
        smt = ArithmeticMean().supported_metric_types
    elif wmc_string.startswith("GeometricMean"):
        smt = GeometricMean().supported_metric_types
    elif wmc_string.startswith("QuadraticMean"):
        smt = QuadraticMean().supported_metric_types
    elif wmc_string.startswith("RotD"):
        smt = RotD(percentile=50.0).supported_metric_types
    else:
        raise ValueError(f"Unsupported WaveformMetricComponent string: {wmc_string}")
    return smt


def xml_string_to_wmc(component_string, channel=None):
    """Helper function to create WaveformMetricComponent from XMLstrings.

    Args:
        component_string (str):
            Old style string representation of component. e.g., "ROTD50.0", "H1".
        channel (str):
            The channel for as-recorded channel components, e.g., "HNN" for "H1".
    """
    component_string = component_string.lower()
    if component_string.startswith("rotd"):
        wmc = RotD(percentile=float(component_string.replace("rotd", "")))
    elif component_string in ["h2", "h1", "z"]:
        wmc = Channels(channel, component_string)
    elif component_string == "arithmeticmean":
        wmc = ArithmeticMean()
    elif component_string == "geometricmean":
        wmc = GeometricMean()
    elif component_string == "quadraticmean":
        wmc = QuadraticMean()
    else:
        raise ValueError(f"Unsupported WaveformMetricComponent: {component_string}")
    return wmc


class WaveformMetricComponent(ABC):
    """Base class for waveform components."""

    def __init__(self):
        self._type = None
        self.supported_metric_types = None
        self.component_attributes = {}
        self._gmpacket_channel_code = ""

    def __repr__(self):
        attr_str = ""
        if self.component_attributes:
            attr_list = []
            for k, val in self.component_attributes.items():
                if isinstance(val, float):
                    val = f"{val:.1f}"
                attr_list.append(f"{k}={val}")
            attr_str = ", ".join(attr_list)
        return f"{self.type}({attr_str})"

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        if not isinstance(other, WaveformMetricComponent):
            raise NotImplementedError()
        return str(self) == str(self)

    def __lt__(self, other):
        return str(self) < str(self)

    @property
    def type(self):
        """Type is the component type and does not include attributes.

        Note that this is the simplest name and we define it to be identical to the
        name of the WaveformMetricComponent subclass.
        """
        return self._type


class Channels(WaveformMetricComponent):
    """WaveformMetricComponent subclass for Channels."""

    def __init__(self, channel, component_string):
        """Channels constructor.

        Args:
            channel (str):
                The trace channel, e.g., HNN.
            component_string (str):
                Simplified component name, e.g., H1.
        """
        super().__init__()
        self._type = self.__class__.__name__
        self.supported_metric_types = [
            "sa",
            "sv",
            "sd",
            "pga",
            "pgv",
            "duration",
            "arias",
            "cav",
        ]
        self.component_attributes["channel"] = channel
        self.component_attributes["component_string"] = component_string
        self._gmpacket_channel_code = component_string

    def __repr__(self):
        attr_str = f"component={self.component_attributes['component_string']}"
        return f"{self.type}({attr_str})"


class ArithmeticMean(WaveformMetricComponent):
    """WaveformMetricComponent subclass for ArithmeticMean."""

    def __init__(self):
        """ArithmeticMean constructor."""
        super().__init__()
        self._type = self.__class__.__name__
        self.supported_metric_types = ["sa", "pga", "pgv", "duration", "arias", "cav"]
        self._gmpacket_channel_code = "amean"


class GeometricMean(WaveformMetricComponent):
    """WaveformMetricComponent subclass for GeometricMean."""

    def __init__(self):
        """GeometricMean constructor."""
        super().__init__()
        self._type = self.__class__.__name__
        self.supported_metric_types = ["sa", "pga", "pgv", "duration", "arias", "cav"]
        self._gmpacket_channel_code = "gmean"


class QuadraticMean(WaveformMetricComponent):
    """WaveformMetricComponent subclass for QuadraticMean."""

    def __init__(self):
        """QuadraticMean constructor."""
        super().__init__()
        self._type = self.__class__.__name__
        self.supported_metric_types = ["fas"]
        self._gmpacket_channel_code = "qmean"


class RotD(WaveformMetricComponent):
    """WaveformMetricComponent subclass for RotD."""

    def __init__(self, percentile):
        """RotD constructor.

        Args:
            percentile (float):
                The RotD percentile.
        """
        super().__init__()
        self._type = self.__class__.__name__
        self.component_attributes["percentile"] = percentile
        self.supported_metric_types = ["sa", "sv", "sd", "pga", "pgv"]
        self._gmpacket_channel_code = f"rotd{int(percentile)}"
