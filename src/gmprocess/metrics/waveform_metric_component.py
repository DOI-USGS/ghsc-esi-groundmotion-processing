"""Module for the WaveformMetricComponent class."""

from abc import ABC


class WaveformMetricComponent(ABC):
    """Base class for waveform components."""

    def __init__(self):
        self._type = None
        self.component_attributes = {}

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

    @property
    def type(self):
        """Type is the component type and does not include attributes.

        Note that this is the simplest name and we define it to be identical to the
        name of the WaveformMetricComponent subclass.
        """
        return self._type


class Channels(WaveformMetricComponent):
    """WaveformMetricComponent subclass for Channels."""

    def __init__(self, channel):
        """Channels constructor.

        Args:
            channel (str):
                The trace channel.
        """
        super().__init__()
        self._type = self.__class__.__name__
        self.component_attributes["channel"] = channel


class GeometricMean(WaveformMetricComponent):
    """WaveformMetricComponent subclass for GeometricMean."""

    def __init__(self):
        """GeometricMean constructor."""
        super().__init__()
        self._type = self.__class__.__name__


class QuadraticMean(WaveformMetricComponent):
    """WaveformMetricComponent subclass for QuadraticMean."""

    def __init__(self):
        """QuadraticMean constructor."""
        super().__init__()
        self._type = self.__class__.__name__


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
