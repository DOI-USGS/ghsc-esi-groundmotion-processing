"""Base class for metric collections"""

from abc import ABC, abstractmethod


class MetricCollection(ABC):
    """Base class for metric collections."""

    @classmethod
    @abstractmethod
    def from_streams(cls, streams):
        """Construct the class from a list of streams"""

    @classmethod
    @abstractmethod
    def from_workspace(cls, workspace):
        """Construct the class from a StreamWorkspace file"""

    @abstractmethod
    def get_metrics_from_workspace(self, workspace):
        """Method for populating metrics collection from the workspace file."""

    @abstractmethod
    def calculate_metrics(self, streams):
        """Calculate waveform metrics from a list of strings."""

    @staticmethod
    def unpack_stream_path(stream_path):
        """Convenience method to unpack the components of the stream path"""
        nslc, eid, label = stream_path.split("_")
        net, sta, loc, chan = nslc.split(".")
        return net, sta, loc, chan, eid, label
