import pytest
import numpy as np
from obspy import UTCDateTime

from gmprocess.waveform_processing import windows


def test_windows_cut(load_data_us1000778i):
    streams, event = load_data_us1000778i
    stream = streams[0]

    st = windows.signal_split(stream, event=event)
    st = windows.signal_end(
        st,
        event_time=UTCDateTime(event.time),
        event_lon=event.longitude,
        event_lat=event.latitude,
        event_mag=event.magnitude,
        method="magnitude",
    )
    windows.cut(st)
    assert st.passed is True
    assert st[0].stats.endtime == UTCDateTime(2016, 11, 13, 11, 6, 20, 340000)
    st_fail = st.copy()
    windows.cut(st_fail, sec_before_split=-10000)
    assert st_fail.passed is False


@pytest.mark.parametrize(
    "method, target",
    [
        pytest.param("noise_duration", "Failed noise window duration check."),
        pytest.param("signal_duration", "Failed signal window duration check."),
    ],
)
def test_windows_durations(method, target, load_data_us1000778i):
    streams, event = load_data_us1000778i
    stream = streams[0].copy()

    stream = windows.signal_split(stream, event=event)
    stream = windows.signal_end(
        stream,
        event_time=UTCDateTime(event.time),
        event_lon=event.longitude,
        event_lat=event.latitude,
        event_mag=event.magnitude,
        method="magnitude",
    )

    if method == "noise_duration":
        windows.window_checks(stream, min_noise_duration=100)
    elif method == "signal_duration":
        windows.window_checks(stream, min_noise_duration=0, min_signal_duration=1000)

    assert stream[0].get_parameter("failure")["reason"] == target


@pytest.mark.parametrize(
    "method, target",
    [
        ("none", [231.685, 231.685, 231.685]),
        ("magnitude", [231.685, 231.685, 231.685]),
        ("velocity", [147.685, 147.685, 147.685]),
        ("model", [241.784936, 241.784936, 241.784936]),
        ("source_path", [243.480171, 243.480171, 243.480171]),
    ],
)
def test_signal_end_methods(method, target, load_data_us1000778i):
    streams, event = load_data_us1000778i
    stream = streams[0]

    stream = windows.signal_split(stream, event=event)

    # Methods = None, magnitude, velocity, and model
    stream = windows.signal_end(
        stream,
        event_time=UTCDateTime(event.time),
        event_lon=event.longitude,
        event_lat=event.latitude,
        event_mag=event.magnitude,
        method=method,
    )
    durations = []
    for tr in stream:
        durations.append(
            tr.get_parameter("signal_end")["end_time"] - UTCDateTime(tr.stats.starttime)
        )
    np.testing.assert_allclose(durations, target)


def test_signal_split2(load_data_us1000778i):
    streams, event = load_data_us1000778i
    streams = streams.copy()

    stream = streams[0]
    windows.signal_split(stream, event)

    cmpdict = {
        "split_time": UTCDateTime(2016, 11, 13, 11, 2, 58, 655000),
        "method": "p_arrival",
        "picker_type": "median(travel_time, ar, baer, power, kalkan)",
    }

    pdict = stream[0].get_parameter("signal_split")
    for key, value in cmpdict.items():
        v1 = pdict[key]
        # because I can't figure out how to get utcdattime __eq__
        # operator to behave as expected with the currently installed
        # version of obspy, we're going to pedantically compare two
        # of these objects...
        if isinstance(value, UTCDateTime):
            # value.__precision = 4
            # v1.__precision = 4
            assert value.year == v1.year
            assert value.month == v1.month
            assert value.day == v1.day
            assert value.hour == v1.hour
            assert value.minute == v1.minute
            assert value.second == v1.second
        else:
            assert v1 == value
