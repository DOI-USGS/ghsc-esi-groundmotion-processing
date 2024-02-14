from gmprocess.metrics import waveform_metric_type
from gmprocess.io.asdf.waveform_metrics_xml import WaveformMetricsXML


def test_waveform_metrics_xml():
    test_sa = waveform_metric_type.SA([0.71], ["H1"], period=1.0)
    test_pga = waveform_metric_type.PGA([0.23], ["Z"])
    mxml = WaveformMetricsXML([test_sa, test_pga])
    xml_str = mxml.to_xml()
    xml_target = (
        '<waveform_metrics><sa units="%g" period="1.000" damping="5.00"><H1>0.71</H1>'
        '</sa><pga units="%g"><Z>0.23</Z></pga></waveform_metrics>'
    )
    assert xml_str == xml_target

    wml = WaveformMetricsXML.from_xml(xml_str)
    assert len(wml.metric_list) == 2
    assert wml.metric_list[0].type == "SA"
    assert wml.metric_list[0].value("Channels(component=h1)") == 0.71
    assert wml.metric_list[1].type == "PGA"
    assert wml.metric_list[1].value("Channels(component=z)") == 0.23
