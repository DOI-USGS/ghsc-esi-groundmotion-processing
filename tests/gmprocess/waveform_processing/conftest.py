import copy

import pytest

from gmprocess.io.read import read_data
from gmprocess.utils.tests_utils import read_data_dir
from gmprocess.core.stationstream import StationStream
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.waveform_processing.windows import (
    signal_split,
    signal_end,
    window_checks,
)
from gmprocess.waveform_processing.snr import compute_snr, snr_check


@pytest.fixture(scope="module")
def geonet_waveforms_nz2018p115908():
    data_files, event = read_data_dir("geonet", "nz2018p115908", "*.V*")
    data_files.sort()
    streams = []
    for f in data_files:
        streams += read_data(f)

    yield streams, event


@pytest.fixture(scope="module")
def fdsn_nc51194936():
    # Returns data and event objects from 3 stations: CVS, GASB, and SBT
    data_files, event = read_data_dir("fdsn", "nc51194936", "*.mseed")
    data_files.sort()
    streams = []
    for f in data_files:
        streams += read_data(f)

    yield streams, event


# Scope to `function` level to prevent mutation of streams when parametrizing tests
@pytest.fixture(scope="function")
def fdsn_ci38457511_CLC():
    # Returns data and event object from a single station as a StationStream
    data_files, event = read_data_dir("fdsn", "ci38457511", "*.mseed")
    data_files.sort()
    streams = []
    for f in data_files:
        # Add trace objects to streams objects
        streams += read_data(f)[0]

    streams = StationStream(streams)
    yield streams, event


@pytest.fixture(scope="module")
def kiknet_usp000hzq8():
    data_files, event = read_data_dir("kiknet", "usp000hzq8")
    data_files.sort()
    streams = []
    for f in data_files:
        streams += read_data(f)

    yield streams, event


@pytest.fixture(scope="module")
def setup_corner_freq_test(load_data_us1000778i, config):
    conf = copy.deepcopy(config)
    streams, event = load_data_us1000778i
    streams = streams.copy()

    window_conf = conf["windows"]

    processed_streams = streams.copy()
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

    for st in processed_streams:
        st = compute_snr(st, event)
    for st in processed_streams:
        st = snr_check(st, mag=event.magnitude)

    yield streams, event, processed_streams


@pytest.fixture(scope="module")
def setup_corner_freq_mag_test(geonet_waveforms_nz2018p115908, config):
    conf = copy.deepcopy(config)

    # Default config has 'constant' corner frequency method, so the need
    # here is to force the 'magnitude' method.
    streams, event = geonet_waveforms_nz2018p115908

    # Select only the V1A files from geonet test data
    # streams = streams[::2]
    sc = StreamCollection(streams)

    window_conf = conf["windows"]

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
