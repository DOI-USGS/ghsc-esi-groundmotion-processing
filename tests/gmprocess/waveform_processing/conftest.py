import pytest

from gmprocess.io.read import read_data
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.utils.config import get_config
from gmprocess.core.streamcollection import StreamCollection

from gmprocess.waveform_processing.windows import signal_split
from gmprocess.waveform_processing.windows import signal_end
from gmprocess.waveform_processing.windows import window_checks

"""
    Fixtures for dealing with Geonet data
"""
@pytest.fixture(scope="module")
def geonet_waveforms():
    data_files, event = read_data_dir("geonet", "us1000778i", "*.V*")
    data_files.sort()
    streams = []
    for f in data_files:
        streams += read_data(f)

    yield streams, event

@pytest.fixture(scope="module")
def geonet_waveforms2():
    data_files, event = read_data_dir("geonet", "nz2018p115908", "*.V*")
    data_files.sort()
    streams = []
    for f in data_files:
        streams += read_data(f)

    yield streams, event

@pytest.fixture(scope="module")
def geonet_single_station():
    data_files, event = read_data_dir("geonet", "us1000778i", "*WTMC*.V1A")
    data_files.sort()
    streams = []
    for f in data_files:
        streams += read_data(f)

    yield streams, event

@pytest.fixture(scope="module")
def geonet_uncorected_waveforms():
    data_files, event = read_data_dir("geonet", "us1000778i", "*.V1A")
    data_files.sort()
    streams = []
    for f in data_files:
        streams += read_data(f)

    yield streams, event

@pytest.fixture(scope="module")
def geonet_corrected_waveforms():
    data_files, event = read_data_dir("geonet", "us1000778i", "*.V2A")
    data_files.sort()
    streams = []
    for f in data_files:
        streams += read_data(f)

    yield streams, event


"""
    Fixtures for dealing with FDSN data
"""
@pytest.fixture(scope="module")
def fdsn_nc51194936():
    data_files, event = read_data_dir("fdsn", "nc51194936", "*.mseed")
    data_files.sort()
    streams = []
    for f in data_files:
        streams += read_data(f)

    yield streams, event

"""
    Fixtures for dealing with KiK-net data
"""
@pytest.fixture(scope="module")
def kiknet_usp000hzq8():
    data_files, event = read_data_dir("kiknet", "usp000hzq8")
    data_files.sort()
    streams = []
    for f in data_files:
        streams += read_data(f)

    yield streams, event

"""
    Test-specific setup fixtures
"""
@pytest.fixture(scope="module")
def setup_corner_freq_test(geonet_waveforms2):
    # Default config has 'constant' corner frequency method, so the need
    # here is to force the 'magnitude' method.
    streams, event = geonet_waveforms2
    
    # Select only the V1A files from geonet test data
    # streams = streams[::2]
    sc = StreamCollection(streams)

    config = get_config()

    window_conf = config["windows"]

    processed_streams = sc.copy()
    for st in processed_streams:
        if st.passed:
            # Estimate noise/signal split time
            st = signal_split(st, event)

            # Estimate end of signal
            end_conf = window_conf["signal_end"]
            event_mag = event.magnitude
            print(st)
            st = signal_end(
                st,
                event_time=event.time,
                event_lon=event.longitude,
                event_lat=event.latitude,
                event_mag=event_mag,
                **end_conf,
            )
            wcheck_conf = window_conf["window_checks"]
            st = window_checks(
                st,
                min_noise_duration=wcheck_conf["min_noise_duration"],
                min_signal_duration=wcheck_conf["min_signal_duration"],
            )
    yield streams, event, processed_streams


@pytest.fixture(scope="module")
def load_integrate_test_waveforms():
    data_files, _ = read_data_dir("geonet", "us1000778i", "*.V1A")
    data_files.sort()
    streams = []
    for f in data_files:
        streams += read_data(f)

    sc = StreamCollection(streams)
    yield sc

# @pytest.fixture(scope="module")
