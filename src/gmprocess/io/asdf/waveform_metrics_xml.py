"""Module for converting waveform metrics dictionaries to XML."""

from lxml import etree

from gmprocess.utils import constants
from gmprocess.io.asdf.base_metrics_xml import MetricXML
from gmprocess.metrics.waveform_metric import WaveformMetric
from gmprocess.metrics.waveform_metric_list import WaveformMetricList

FLOAT_ATTRIBUTES = ["period", "damping"]


class WaveformMetricsXML(MetricXML):
    """Class for converting a waveform metrics dictionary to/from XML."""

    def __init__(self, metric_list):
        """Construct a WaveformMetricsXML instance.

        Args:
            metric_list (list):
                List of WaveformMetric objects.
        """
        if not all(isinstance(wm, WaveformMetric) for wm in metric_list):
            raise TypeError("All elements of metric_list must be a WaveformMetric.")
        self.metric_list = metric_list

    def to_xml(self):
        """Output the waveform metric in an xml format."""
        root = etree.Element("waveform_metrics")
        for wm in self.metric_list:
            imtstr = wm.type.lower()
            units = wm.units

            attrs = wm.metric_attributes

            fmt = constants.METRICS_XML_FLOAT_STRING_FORMAT

            attdict = {"units": units}

            for att, atval in attrs.items():
                if isinstance(atval, str):
                    attdict[att] = atval
                else:
                    attdict[att] = fmt[att] % atval

            imt_tag = etree.SubElement(root, imtstr, attrib=attdict)

            for i, imc in enumerate(wm.components):
                imcstr = imc.lower().replace("(", "").replace(")", "")
                if wm.component_to_channel and imc in wm.component_to_channel:
                    attributes = {"original_channel": wm.component_to_channel[imc]}
                else:
                    attributes = {}
                imc_tag = etree.SubElement(imt_tag, imcstr, attrib=attributes)
                imc_tag.text = fmt[wm.format_type] % wm.value(imc)
        return etree.tostring(root, encoding="unicode")

    @classmethod
    def from_xml(cls, xml_str):
        """Construct a WaveformMetricList object from xml.

        Args:
            xml_str (str):
                XML string.

        Returns:
            WaveformMetricList
        """
        root = etree.fromstring(xml_str)
        metric_list = []
        for element in root.getchildren():
            etag = element.tag
            units = element.attrib["units"]
            element.attrib.pop("units")
            comp_to_chan = {}
            mvalues = []
            mcomps = []
            for imc_element in element.getchildren():
                imc = imc_element.tag.upper()
                if imc in ["H1", "H2", "Z"]:
                    if "original_channel" in imc_element.attrib:
                        comp_to_chan[imc] = imc_element.attrib["original_channel"]
                mcomps.append(imc)
                mvalues.append(float(imc_element.text))

            att_dict = dict(element.attrib)
            for aname, aval in att_dict.items():
                if aname in FLOAT_ATTRIBUTES:
                    att_dict[aname] = float(aval)

            mdict = {
                "values": mvalues,
                "components": mcomps,
                "type": etag2type(etag),
                "format_type": "",
                "units": units,
                "metric_attributes": att_dict,
                "component_to_channel": comp_to_chan,
            }
            metric_list.append(WaveformMetric.metric_from_dict(mdict))
        return WaveformMetricList(metric_list)


def etag2type(etag):
    """Convenience method for converting etag to type.

    Probably need a better system for this. Also note that we do something similar
    in the WaveformMetricList class.
    """
    etag = etag.lower()
    if etag.startswith("sa"):
        etag_type = "SA"
    elif etag.startswith("fas"):
        etag_type = "FAS"
    elif etag.startswith("duration"):
        etag_type = "Duration"
    elif etag.startswith("sorted"):
        etag_type = "SortedDuration"
    elif etag.startswith("arias"):
        etag_type = "AriasIntensity"
    else:
        etag_type = etag.upper()
    return etag_type
