#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from gmprocess.metrics import metrics
from gmprocess.io.asdf.metrics_xml import MetricsXML


def test_metrics_xml():
    test_sa = metrics.SA([0.71], ["H1"], period=1.0)
    test_sa_dict = test_sa.to_dict()
    mxml = MetricsXML(test_sa_dict)
    xml_str = mxml.to_xml()
    xml_target = (
        '<waveform_metrics><sa units="%g" period="1.000" damping="5.00">'
        "<h1>0.71</h1></sa></waveform_metrics>"
    )
    assert xml_str == xml_target


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_metrics_xml()
