#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from gmprocess.metrics import waveform_metric
from gmprocess.io.asdf.waveform_metrics_xml import WaveformMetricsXML


def test_waveform_metrics_xml():
    test_sa = waveform_metric.SA([0.71], ["H1"], period=1.0)
    test_pga = waveform_metric.PGA([0.23], ["Z"])
    mxml = WaveformMetricsXML([test_sa, test_pga])
    xml_str = mxml.to_xml()
    xml_target = (
        '<waveform_metrics><sa units="%g" period="1.000" damping="5.00"><h1>0.71</h1>'
        '</sa><pga units="%g"><z>0.23</z></pga></waveform_metrics>'
    )
    assert xml_str == xml_target

    wml = WaveformMetricsXML.from_xml(xml_str)
    assert len(wml.metric_list) == 2
    assert wml.metric_list[0].type == "SA"
    assert wml.metric_list[0].values["H1"] == 0.71
    assert wml.metric_list[1].type == "PGA"
    assert wml.metric_list[1].values["Z"] == 0.23


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_waveform_metrics_xml()