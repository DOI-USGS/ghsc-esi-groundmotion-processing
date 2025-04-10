import numpy as np
from obspy.core.utcdatetime import UTCDateTime
from obspy.core.trace import Trace

from gmprocess.core.stationstream import StationStream

from invutils import get_inventory


def test_warning(load_data_uw61251926):
    st = load_data_uw61251926[0]
    warnings1 = st[0].get_parameter("warnings")
    assert warnings1 == []
    st[0].warning({"warning 1"})
    st[0].warning({"warning 2"})
    warnings2 = st[0].get_parameter("warnings")
    assert len(warnings2) == 2


def test_stream():
    inventory = get_inventory()
    channels = ["HN1", "HN2", "HNZ"]
    data = np.random.rand(1000)
    traces = []
    network = inventory.networks[0]
    station = network.stations[0]
    chlist = station.channels
    channelcodes = [ch.code for ch in chlist]
    for channel in channels:
        chidx = channelcodes.index(channel)
        channeldata = chlist[chidx]
        header = {
            "sampling_rate": channeldata.sample_rate,
            "npts": len(data),
            "network": network.code,
            "location": channeldata.location_code,
            "station": station.code,
            "channel": channel,
            "starttime": UTCDateTime(2010, 1, 1, 0, 0, 0),
        }
        trace = Trace(data=data, header=header)
        traces.append(trace)
    invstream = StationStream(traces=traces, inventory=inventory)
    inventory2 = invstream.get_inventory()
    inv2_channel1 = inventory2.networks[0].stations[0].channels[0]
    inv_channel1 = inventory2.networks[0].stations[0].channels[0]
    assert inv_channel1.code == inv2_channel1.code

    # test the streamparam functionality
    statsdict = {"name": "Fred", "age": 34}
    invstream.set_stream_param("stats", statsdict)
    stream_params = invstream.get_stream_param_keys()
    stream_params.sort()
    assert stream_params == ["any_trace_failures", "stats"]
    cmpdict = invstream.get_stream_param("stats")
    assert statsdict == cmpdict


def test_uneven_stream():
    inventory = get_inventory()
    channels = ["HN1", "HN2", "HNZ"]
    data1 = np.random.rand(1000)
    data2 = np.random.rand(1001)
    data3 = np.random.rand(1002)
    data = [data1, data2, data3]
    traces = []
    network = inventory.networks[0]
    station = network.stations[0]
    chlist = station.channels
    channelcodes = [ch.code for ch in chlist]
    for datat, channel in zip(data, channels):
        chidx = channelcodes.index(channel)
        channeldata = chlist[chidx]
        header = {
            "sampling_rate": channeldata.sample_rate,
            "npts": len(datat),
            "network": network.code,
            "location": channeldata.location_code,
            "station": station.code,
            "channel": channel,
            "starttime": UTCDateTime(2010, 1, 1, 0, 0, 0),
        }
        trace = Trace(data=datat, header=header)
        traces.append(trace)
    StationStream(traces=traces, inventory=inventory)


def test_num_horizontals(load_data_uw61251926):
    sc = load_data_uw61251926
    st = sc.select(station="SP2")[0]
    assert st.num_horizontal == 2

    for tr in st:
        tr.stats.channel = "ENZ"
    assert st.num_horizontal == 0

    for tr in st:
        tr.stats.channel = "EN1"
    assert st.num_horizontal == 3
