"""Module for converting waveform metrics dictionaries to XML."""

import logging
from lxml import etree
import numpy as np

from gmprocess.utils import constants
from gmprocess.io.asdf.base_metrics_xml import MetricXML
from gmprocess.metrics.waveform_metric_type import WaveformMetricType
from gmprocess.metrics.waveform_metric_list import WaveformMetricList
from gmprocess.metrics.utils import component_to_channel
from gmprocess.metrics.containers import CombinedSpectra, FourierSpectra
from gmprocess.metrics.waveform_metric_component import xml_string_to_wmc, RotD

FLOAT_ATTRIBUTES = ["period", "damping"]


class WaveformMetricsXML(MetricXML):
    """Class for converting a waveform metrics dictionary to/from XML."""

    def __init__(self, metric_list):
        """Construct a WaveformMetricsXML instance.

        Args:
            metric_list (list):
                List of WaveformMetric objects.
        """
        if not all(isinstance(wm, WaveformMetricType) for wm in metric_list):
            raise TypeError("All elements of metric_list must be a WaveformMetric.")
        self.metric_list = metric_list

    def to_xml(self):
        """Output the waveform metric in an xml format."""
        fmt = constants.METRICS_XML_FLOAT_STRING_FORMAT
        root = etree.Element("waveform_metrics")
        for wm in self.metric_list:
            imtstr = wm.type.lower()
            units = wm.units
            attrs = wm.metric_attributes
            attdict = {"units": units}
            for att, atval in attrs.items():
                if isinstance(atval, str):
                    attdict[att] = atval
                else:
                    attdict[att] = fmt[att] % atval

            imt_tag = etree.SubElement(root, imtstr, attrib=attdict)

            # Collect the channels and get the simplified components
            channel_names = []
            for imc in wm.components:
                if imc.startswith("Channels"):
                    channel_names.append(imc.split("=")[1].replace(")", ""))
            _, reverse_dict = component_to_channel(channel_names)

            for imc in wm.components:
                if imc.startswith("Channels"):
                    orig_imc_str = imc.split("=")[1].replace(")", "")
                    imc_str = reverse_dict[orig_imc_str]
                    attributes = {"original_channel": orig_imc_str}
                elif imc.startswith("RotD"):
                    imc_str = "RotD"
                    percentile = imc.split("=")[1].replace(")", "")
                    attributes = {"percentile": percentile}
                else:
                    imc_str = imc.replace("()", "")
                    attributes = {}
                imc_tag = etree.SubElement(imt_tag, imc_str, attrib=attributes)
                if isinstance(wm.value(imc), (CombinedSpectra, FourierSpectra)):
                    ctr = wm.value(imc)
                    freq_tag = etree.SubElement(imc_tag, "frequency")
                    freq_tag.text = (
                        np.array2string(ctr.frequency, max_line_width=np.inf)
                        .replace("[", "")
                        .replace("]", "")
                    )
                    spec_tag = etree.SubElement(imc_tag, "fourier_spectra")
                    spec_array = ctr.fourier_spectra
                    if isinstance(spec_array, list):
                        spec_array = spec_array[0]
                    spec_tag.text = (
                        np.array2string(spec_array, max_line_width=np.inf)
                        .replace("[", "")
                        .replace("]", "")
                    )
                else:
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
                imc_chan = None
                if imc in ["H1", "H2", "Z"]:
                    if "original_channel" in imc_element.attrib:
                        comp_to_chan[imc] = imc_element.attrib["original_channel"]
                        imc_chan = comp_to_chan[imc]
                if "percentile" in imc_element.attrib:
                    mcomps.append(
                        RotD(percentile=float(imc_element.attrib["percentile"]))
                    )
                else:
                    mcomps.append(xml_string_to_wmc(imc, imc_chan))
                # For, FAS, imc_element will have additional children for frequency and
                # spectra.
                if etag.lower() == "fas":
                    try:
                        fas = imc_element.getchildren()
                        frequency = np.fromstring(fas[0].text, sep=" ")
                        spectra = np.fromstring(fas[1].text, sep=" ")
                        mvalues.append(CombinedSpectra(frequency, spectra))
                    except IndexError:
                        logging.warning("Cannot parse FAS from old ASDF format.")
                else:
                    mvalues.append(float(imc_element.text))

            att_dict = dict(element.attrib)
            for aname, aval in att_dict.items():
                if aname in FLOAT_ATTRIBUTES:
                    att_dict[aname] = float(aval)

            if etag.lower() == "fas":
                att_dict["frequencies"] = {}

            mdict = {
                "values": mvalues,
                "components": mcomps,
                "type": etag2type(etag),
                "format_type": "",
                "units": units,
                "metric_attributes": att_dict,
                "component_to_channel": comp_to_chan,
            }
            metric_list.append(WaveformMetricType.metric_from_dict(mdict))
        return WaveformMetricList(metric_list)


def etag2type(etag):
    """Convenience method for converting etag to type.

    Probably need a better system for this. Also note that we do something similar
    in the WaveformMetricList class.
    """
    etag = etag.lower()
    if etag.startswith("sa"):
        etag_type = "sa"
    elif etag.startswith("sv"):
        etag_type = "sv"
    elif etag.startswith("sd"):
        etag_type = "sd"
    elif etag.startswith("fas"):
        etag_type = "fas"
    elif etag.startswith("duration"):
        etag_type = "duration"
    elif etag.startswith("sorted"):
        etag_type = "SortedDuration"
    elif etag.startswith("arias"):
        etag_type = "Arias"
    elif etag.startswith("cav"):
        etag_type = "CAV"
    else:
        etag_type = etag.upper()
    return etag_type
