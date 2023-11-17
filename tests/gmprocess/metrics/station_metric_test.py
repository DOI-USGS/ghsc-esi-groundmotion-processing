from gmprocess.metrics.station_metric import StationMetric


def test_station_metric():
    station_metric_dict = {
        "repi": 10.0,
        "rhyp": 12.0,
        "rrup_mean": 12.0,
        "rrup_var": 0.0,
        "rjb_mean": 10.0,
        "rjb_var": 0.0,
        "gc2_rx": 0.0,
        "gc2_ry": 10.0,
        "gc2_ry0": 10.0,
        "gc2_U": 10.0,
        "gc2_T": 0.0,
        "back_azimuth": 0.0,
    }
    sta_metric = StationMetric(**station_metric_dict)
    repr_target = (
        "StationMetric(repi=10.0, rhyp=12.0, rrup_mean=12.0, rrup_var=0.0, "
        "rjb_mean=10.0, rjb_var=0.0, gc2_rx=0.0, gc2_ry=10.0, gc2_ry0=10.0, "
        "gc2_U=10.0, gc2_T=0.0, back_azimuth=0.0)"
    )
    assert sta_metric.__repr__() == repr_target
    test_metric_dict = sta_metric.to_dict()
    assert test_metric_dict["repi"] == 10.0
