"""Base class for converting metrics dictionaries to XML."""

from abc import ABC, abstractmethod


class MetricXML(ABC):
    """Base class for converting metrics dictionaries to XML."""

    @abstractmethod
    def to_xml(self):
        """Convert metrics to XML"""

    @classmethod
    @abstractmethod
    def from_xml(cls, xml_str):
        """Convert metrics to XML"""
