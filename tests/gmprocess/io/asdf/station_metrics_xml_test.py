#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from gmprocess.metrics import station_metric
from gmprocess.io.asdf.station_metrics_xml import StationMetricsXML


def test_station_metrics_xml():
    test_sm1 = station_metric.StationMetric(
        repi=10.0,
        rhyp=12.0,
        rrup_mean=12.0,
        rrup_var=0.0,
        rjb_mean=10.0,
        rjb_var=0.0,
        gc2_rx=0.0,
        gc2_ry=10.0,
        gc2_ry0=10.0,
        gc2_U=10.0,
        gc2_T=0.0,
        back_azimuth=0.0,
    )
    test_sm_dict = test_sm1.to_dict()
    assert test_sm_dict["repi"] == 10.0

    sxml = StationMetricsXML(test_sm1)

    xml_str = sxml.to_xml()
    xml_target = (
        '<station_metrics><distances><epicentral units="km">10.00</epicentral>'
        '<hypocentral units="km">12.00</hypocentral><rupture units="km">12.00'
        '</rupture><rupture_var units="km">0.00</rupture_var><joyner_boore units="km">'
        '10.00</joyner_boore><joyner_boore_var units="km">0.00</joyner_boore_var>'
        '<gc2_rx units="km">0.00</gc2_rx><gc2_ry units="km">10.00</gc2_ry>'
        '<gc2_ry0 units="km">10.00</gc2_ry0><gc2_U units="km">10.00</gc2_U>'
        '<gc2_T units="km">0.00</gc2_T></distances><back_azimuth>0.00</back_azimuth>'
        "</station_metrics>"
    )
    assert xml_str == xml_target

    sxml2 = StationMetricsXML.from_xml(xml_str)
    assert sxml2.metrics.rjb_mean == 10.0


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_station_metrics_xml()
