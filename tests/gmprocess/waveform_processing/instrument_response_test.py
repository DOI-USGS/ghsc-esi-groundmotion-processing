from gmprocess.utils.constants import TEST_DATA_DIR
from gmprocess.io.read import read_data
from gmprocess.waveform_processing.instrument_response import remove_response


def test_differing_sensitivity(capsys):
    dfile = (
        TEST_DATA_DIR
        / "differing_sensitivity"
        / "CI.Q0056.01.HNE__20190706T031923Z__20190706T032653Z.mseed"
    )
    stream = read_data(dfile)[0]
    trace_warnings = stream[0].get_parameter("warnings")
    assert trace_warnings == []

    with capsys.disabled():
        stream2 = remove_response(stream)

    trace_warnings = stream2[0].get_parameter("warnings")
    assert trace_warnings[0]["reason"] == "Computed and reported sensitivities differ."

    assert stream2.warnings == ["Computed and reported sensitivities differ."]
