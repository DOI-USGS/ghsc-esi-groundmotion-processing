# stdlib imports
import os
import copy

# third party imports
import h5py
import pytest

from gmprocess.io.asdf.core import write_asdf
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.io.asdf.waveform_metrics_xml import WaveformMetricsXML
from gmprocess.io.asdf.station_metrics_xml import StationMetricsXML
from gmprocess.utils import constants
from gmprocess.metrics.waveform_metric_collection import WaveformMetricCollection
from gmprocess.metrics.station_metric_collection import StationMetricCollection
from gmprocess.waveform_processing.processing import process_streams


@pytest.fixture
def generate_workspace(config, load_data_us1000778i, tmp_path, configure_strec):
    """Generate simple HDF5 with ASDF layout for testing."""
    conf = copy.deepcopy(config)
    existing_config_data = configure_strec
    streams, event = load_data_us1000778i
    streams = streams.copy()

    EVENTID = "us1000778i"
    LABEL = "ptest"

    tfilename = tmp_path / "workspace.h5"

    try:
        write_asdf(tfilename, streams, event, label="unprocessed")

        # Simplify for tests
        conf["metrics"]["type_parameters"]["sa"]["periods"] = [1.0, 2.0, 3.0]
        conf["metrics"]["type_parameters"]["fas"]["frequencies"] = {
            "start": 0.1,
            "stop": 1.0,
            "num": 11,
        }
        workspace = StreamWorkspace.open(tfilename)
        raw_streams = workspace.get_streams(
            EVENTID, labels=["unprocessed"], config=conf
        )
        pstreams = process_streams(raw_streams, event, config=conf)
        workspace.add_streams(event, pstreams, label=LABEL)
        workspace.add_config(conf)

        wmc = WaveformMetricCollection.from_streams(pstreams, event, conf, LABEL)
        for wm, sp in zip(wmc.waveform_metrics, wmc.stream_paths):
            wxml = WaveformMetricsXML(wm.metric_list)
            xmlstr = wxml.to_xml()
            workspace.insert_aux(xmlstr, "WaveFormMetrics", sp)

        smc = StationMetricCollection.from_streams(pstreams, event, conf)
        for sm, sp in zip(smc.station_metrics, smc.stream_paths):
            sxml = StationMetricsXML(sm)
            xmlstr = sxml.to_xml()
            workspace.insert_aux(xmlstr, "StationMetrics", sp)
        workspace.close()
    finally:
        if existing_config_data is not None:
            with open(constants.STREC_CONFIG_PATH, "wt", encoding="utf-8") as f:
                f.write(existing_config_data)

    yield tfilename


def test_layout(generate_workspace):
    LAYOUT_FILENAME = "asdf_layout.txt"

    tfilename = generate_workspace
    h5 = h5py.File(tfilename, "r")
    # To regenerate an updated version of the asdf_layout.txt file:
    #   - Install hdf5 command line tools,
    #   - h5dump -n workspace.h5 > asdf_layout.txt
    #   - Clean up extra content
    testroot = str(constants.TEST_DATA_DIR / "asdf")
    layout_abspath = os.path.join(testroot, LAYOUT_FILENAME)
    with open(layout_abspath, "r", encoding="utf-8") as fin:
        lines = fin.readlines()
        for line in lines:
            assert line.strip() in h5
    h5.close()
    return
