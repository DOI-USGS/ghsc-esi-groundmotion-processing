#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import copy
from obspy import UTCDateTime

from gmprocess.core.stationstream import StationStream
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.io.read import read_data
from gmprocess.utils.config import get_config
from gmprocess.utils.constants import TEST_DATA_DIR
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.waveform_processing import windows


PICKER_CONFIG = get_config()["pickers"]

data_path = TEST_DATA_DIR / "process"


def test_windows():
    datafiles, event = read_data_dir("fdsn", "ci38457511", "*.mseed")
    trace_list = []
    for datafile in datafiles:
        trace_list.append(read_data(datafile)[0][0])
    st = StationStream(copy.deepcopy(trace_list))
    st = windows.signal_split(st, event=event)
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
    assert st[0].stats.endtime == "2019-07-06T03:22:55.998300Z"
    st_fail = st.copy()
    windows.cut(st_fail, sec_before_split=-10000)
    assert st_fail.passed is False

    st2 = StationStream(copy.deepcopy(trace_list))
    windows.window_checks(st2)
    assert (
        st2[0].get_parameter("failure")["reason"]
        == "Cannot check window because no split time available."
    )

    st3 = StationStream(copy.deepcopy(trace_list))
    st3 = windows.signal_split(st3, event=event)
    st3 = windows.signal_end(
        st3,
        event_time=UTCDateTime(event.time),
        event_lon=event.longitude,
        event_lat=event.latitude,
        event_mag=event.magnitude,
        method="magnitude",
    )
    windows.window_checks(st3, min_noise_duration=100)
    assert (
        st3[0].get_parameter("failure")["reason"]
        == "Failed noise window duration check."
    )

    st4 = StationStream(copy.deepcopy(trace_list))
    st4 = windows.signal_split(st4, event=event)
    st4 = windows.signal_end(
        st4,
        event_time=UTCDateTime(event.time),
        event_lon=event.longitude,
        event_lat=event.latitude,
        event_mag=event.magnitude,
        method="magnitude",
    )
    windows.window_checks(st4, min_signal_duration=1000)
    assert (
        st4[0].get_parameter("failure")["reason"]
        == "Failed signal window duration check."
    )


def test_signal_end():
    datafiles, event = read_data_dir("fdsn", "ci38457511", "*.mseed")
    streams = []
    for datafile in datafiles:
        streams.append(read_data(datafile)[0][0])
    old_durations = []
    for tr in streams:
        old_durations.append((tr.stats.npts - 1) * tr.stats.delta)
    new_streams = windows.signal_split(streams, event=event)

    # Method = none
    new_streams = windows.signal_end(
        new_streams,
        event_time=UTCDateTime(event.time),
        event_lon=event.longitude,
        event_lat=event.latitude,
        event_mag=event.magnitude,
        method="none",
    )
    new_durations = []
    for tr in new_streams:
        new_durations.append(
            tr.get_parameter("signal_end")["end_time"] - UTCDateTime(tr.stats.starttime)
        )
    np.testing.assert_allclose(new_durations, old_durations)

    # Method = magnitude
    new_streams = windows.signal_end(
        new_streams,
        event_time=UTCDateTime(event.time),
        event_lon=event.longitude,
        event_lat=event.latitude,
        event_mag=event.magnitude,
        method="magnitude",
    )
    new_durations = []
    for tr in new_streams:
        new_durations.append(
            tr.get_parameter("signal_end")["end_time"] - UTCDateTime(tr.stats.starttime)
        )
    target = np.array([212.9617, 212.9617, 212.9617])
    np.testing.assert_allclose(new_durations, target)

    # Method = velocity
    new_streams = windows.signal_end(
        new_streams,
        event_time=UTCDateTime(event.time),
        event_lon=event.longitude,
        event_lat=event.latitude,
        event_mag=event.magnitude,
        method="velocity",
    )
    new_durations = []
    for tr in new_streams:
        new_durations.append(
            tr.get_parameter("signal_end")["end_time"] - UTCDateTime(tr.stats.starttime)
        )
    target = np.array([149.9617, 149.9617, 149.9617])
    np.testing.assert_allclose(new_durations, target)

    # Method = model
    new_streams = windows.signal_end(
        new_streams,
        event_time=UTCDateTime(event.time),
        event_lon=event.longitude,
        event_lat=event.latitude,
        event_mag=event.magnitude,
        method="model",
    )
    new_durations = []
    for tr in new_streams:
        new_durations.append(
            tr.get_parameter("signal_end")["end_time"] - UTCDateTime(tr.stats.starttime)
        )
    target = np.array([89.008733, 89.008733, 89.008733])
    np.testing.assert_allclose(new_durations, target)


def test_signal_split2():
    datafiles, event = read_data_dir("knet", "us2000cnnl", "AOM0011801241951*")
    streams = []
    for datafile in datafiles:
        streams += read_data(datafile)

    streams = StreamCollection(streams)
    stream = streams[0]
    windows.signal_split(stream, event)

    cmpdict = {
        "split_time": UTCDateTime(2018, 1, 24, 10, 51, 38, 841483),
        "method": "p_arrival",
        "picker_type": "travel_time",
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


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_signal_split2()
    test_signal_end()
    test_windows()
