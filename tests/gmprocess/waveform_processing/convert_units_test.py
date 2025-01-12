from gmprocess.waveform_processing.convert_units import convert_to_acceleration
from gmprocess.io.read import read_data
from gmprocess.utils.constants import TEST_DATA_DIR


def test_convert_to_acceleration(config):
    mfile = "BK.SCZ.00.BHE__20140824T102014Z__20140824T102815Z.mseed"
    streams = read_data(TEST_DATA_DIR / "convert_units" / mfile)
    stream = streams[0]

    assert stream[0].stats.standard.units == "raw counts"

    stream = convert_to_acceleration(stream, config=config)

    assert stream[0].stats.standard.units == "raw counts/s"
