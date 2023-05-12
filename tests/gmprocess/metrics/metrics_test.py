#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from gmprocess.metrics import metrics


def test_metrics():
    test_sa = metrics.SA([0.71], ["H1"], period=1.0)
    assert test_sa.__repr__() == "SA(T=1.0000, D=5.000)"
    xml_str = test_sa.to_xml()
    xml_target = (
        '<waveform_metrics><sa units="%g" period="1.000" damping="5.00">'
        "<h1>0.71</h1></sa></waveform_metrics>"
    )
    assert xml_str == xml_target

    test_pga = metrics.PGA([0.14], ["H1"])
    assert test_pga.__repr__() == "PGA"
    xml_str = test_pga.to_xml()
    xml_target = (
        '<waveform_metrics><pga units="%g"><h1>0.14</h1></pga></waveform_metrics>'
    )
    assert xml_str == xml_target

    test_pgv = metrics.PGV([0.23], ["H2"])
    assert test_pgv.__repr__() == "PGV"
    xml_str = test_pgv.to_xml()
    xml_target = (
        '<waveform_metrics><pgv units="cm/s"><h2>0.23</h2></pgv></waveform_metrics>'
    )
    assert xml_str == xml_target

    test_duration = metrics.Duration([3.24], ["H2"], "5-95")
    assert test_duration.__repr__() == "Duration(5-95)"
    xml_str = test_duration.to_xml()
    xml_target = (
        '<waveform_metrics><duration units="s" interval="5-95">'
        "<h2>3.24</h2></duration></waveform_metrics>"
    )
    assert xml_str == xml_target


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_metrics()
