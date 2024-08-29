"""Module for converting station metrics dictionaries to XML"""

from lxml import etree

from gmprocess.utils import constants
from gmprocess.io.asdf.base_metrics_xml import MetricXML
from gmprocess.metrics.station_metric import StationMetric


class StationMetricsXML(MetricXML):
    """Class for converting a station metrics dictionary to/from XML"""

    # Need to have this list to know which metrics to put in the "distances" element
    # and also for mapping the "short" name in the dictionary keys to the "long"
    # name in the xml string.
    dist_metrics = {
        "repi": "epicentral",
        "rhyp": "hypocentral",
        "rrup_mean": "rupture",
        "rrup_var": "rupture_var",
        "rjb_mean": "joyner_boore",
        "rjb_var": "joyner_boore_var",
        "gc2_rx": None,
        "gc2_ry": None,
        "gc2_ry0": None,
        "gc2_U": None,
        "gc2_T": None,
    }

    def __init__(self, metrics):
        """Construct a StationMetricsXML instance.

        Args:
            metrics (list):
                A StationMetric object.
        """
        self.metrics = metrics

    def to_xml(self):
        """Output the station metric in an xml format."""
        root = etree.Element("station_metrics")
        dist_element = etree.SubElement(root, "distances")
        for met_name, met_val in self.metrics.to_dict().items():
            if met_name in self.dist_metrics:
                long_name = met_name
                if (
                    long_name in self.dist_metrics
                    and self.dist_metrics[long_name] is not None
                ):
                    long_name = self.dist_metrics[long_name]
                element = etree.SubElement(dist_element, long_name, units="km")
                element.text = (
                    constants.METRICS_XML_FLOAT_STRING_FORMAT["distance"] % met_val
                )
            else:
                element = etree.SubElement(root, met_name)
                element.text = (
                    constants.METRICS_XML_FLOAT_STRING_FORMAT["distance"] % met_val
                )
        return etree.tostring(root, encoding="unicode")

    @classmethod
    def from_xml(cls, xml_str):
        """Construct a StationMetricsXML object from xml.

        Args:
            xml_str (str):
                XML string.
        """
        root = etree.fromstring(xml_str)
        for element in root.getchildren():
            etag = element.tag
            if etag == "back_azimuth":
                back_azimuth = float(element.text)
            elif etag == "distances":
                dist_dict = {}
                for dist_element in element.getchildren():
                    dist_dict[dist_element.tag] = float(dist_element.text)

        for dist_short, dist_long in cls.dist_metrics.items():
            if dist_long is not None and dist_long in dist_dict:
                dist_dict[dist_short] = dist_dict[dist_long]
                dist_dict.pop(dist_long)

        sm = StationMetric(**dist_dict, back_azimuth=back_azimuth)
        return cls(sm)
