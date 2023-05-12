"""Module for converting metrics dictionaries to XML"""

from lxml import etree

from gmprocess.utils import constants


class MetricsXML(object):
    """Class for converting a metrics dictionary to XML"""

    def __init__(self, dict):
        """Construct a MetricsXML instance.

        Args:
            dict (dict):
                Dictionary with structure that matches the output of the `to_dict`
                methoc of the gmprocess.metrics.metric.Metric module.
        """

        self.type = dict["type"]
        self.units = dict["units"]
        self.values = dict["values"]
        self.components = dict["components"]
        self.metric_attributes = dict["metric_attributes"]
        self.format_type = dict["format_type"]
        self.component_to_channel = dict["component_to_channel"]

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

        for i, imc in enumerate(self.components):
            imcstr = imc.lower().replace("(", "").replace(")", "")
            if self.component_to_channel and imc in self.component_to_channel:
                attributes = {"original_channel": self.component_to_channel[imc]}
            else:
                attributes = {}
            imc_tag = etree.SubElement(imt_tag, imcstr, attrib=attributes)
            imc_tag.text = fmt[self.format_type] % self.values[i]
        return etree.tostring(root, encoding="unicode")
