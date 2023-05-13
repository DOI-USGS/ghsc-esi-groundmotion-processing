#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from gmprocess.metrics import metrics


def test_metrics():
    test_sa = metrics.SA([0.71], ["H1"], period=1.0)
    assert test_sa.__repr__() == "SA(T=1.0000, D=5.000): H1=0.710"
    assert test_sa.identifier == "SA(T=1.0000, D=5.000)"
    assert test_sa.units == "%g"
    assert test_sa.value("H1") == 0.71

    test_sa_dict = test_sa.to_dict()
    test_sa2 = metrics.Metric.metric_from_dict(test_sa_dict)
    assert test_sa2.__repr__() == "SA(T=1.0000, D=5.000): H1=0.710"

    test_pga = metrics.PGA([0.14, 0.2], ["H1", "H2"])
    assert test_pga.values["H1"] == 0.14
    comps = test_pga.components
    assert len(comps) == 2
    assert "H1" in comps and "H2" in comps

    test_pgv = metrics.PGV([0.23], ["H2"])
    assert test_pgv.__repr__() == "PGV: H2=0.230"

    test_duration = metrics.Duration([3.24], ["H2"], "5-95")
    assert test_duration.__repr__() == "Duration(5-95): H2=3.240"


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_metrics()
