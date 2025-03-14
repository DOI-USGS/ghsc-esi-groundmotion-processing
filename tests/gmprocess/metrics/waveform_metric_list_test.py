from gmprocess.metrics import waveform_metric_type
from gmprocess.metrics.waveform_metric_list import WaveformMetricList


def test_metrics_list():
    test_sa = waveform_metric_type.SA([0.71], ["H1"], period=1.0)
    test_pga = waveform_metric_type.PGA([0.23], ["Z"])
    wml = WaveformMetricList([test_sa, test_pga])
    repr_target = (
        "2 metric(s) in list:\n  SA(T=1.0000, D=5.000): H1=0.710\n  PGA: Z=0.230\n"
    )
    assert wml.__repr__() == repr_target

    test_df = wml.to_df()
    assert test_df.shape == (2, 3)

    wml2 = WaveformMetricList.from_df(test_df)
    assert len(wml2.metric_list) == 2
    assert wml2.__repr__() == repr_target
