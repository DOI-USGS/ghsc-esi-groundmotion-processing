# stdlib imports
import os

# third party imports
import h5py
import pytest

from gmprocess.io.asdf.core import write_asdf
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.io.asdf.waveform_metrics_xml import WaveformMetricsXML
from gmprocess.io.asdf.station_metrics_xml import StationMetricsXML
from gmprocess.utils.config import update_config
from gmprocess.utils import constants
from gmprocess.metrics.waveform_metric_collection import WaveformMetricCollection
from gmprocess.metrics.station_metric_collection import StationMetricCollection
from gmprocess.waveform_processing.processing import process_streams


@pytest.fixture
def generate_workspace(config, load_data_us1000778i, tmp_path, configure_strec):
    """Generate simple HDF5 with ASDF layout for testing."""
    EVENTID = "us1000778i"
    LABEL = "ptest"
    streams, event = load_data_us1000778i

    tfilename = tmp_path / "workspace.h5"

    existing_config_data = configure_strec
    try:
        write_asdf(tfilename, streams, event, label="unprocessed")

        config = update_config(
            str(constants.TEST_DATA_DIR / "config_min_freq_0p2.yml"), config
        )

        workspace = StreamWorkspace.open(tfilename)
        raw_streams = workspace.get_streams(
            EVENTID, labels=["unprocessed"], config=config
        )
        pstreams = process_streams(raw_streams, event, config=config)
        workspace.add_streams(event, pstreams, label=LABEL)
        workspace.add_config(config)

        wmc = WaveformMetricCollection.from_streams(pstreams, event, config, LABEL)
        for wm, sp in zip(wmc.waveform_metrics, wmc.stream_paths):
            wxml = WaveformMetricsXML(wm.metric_list)
            xmlstr = wxml.to_xml()
            workspace.insert_aux(xmlstr, "WaveFormMetrics", sp)

        smc = StationMetricCollection.from_streams(pstreams, event, config)
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

    testroot = str(constants.TEST_DATA_DIR / "asdf")
    layout_abspath = os.path.join(testroot, LAYOUT_FILENAME)
    with open(layout_abspath, "r", encoding="utf-8") as fin:
        lines = fin.readlines()
        for line in lines:
            assert line.strip() in h5
    h5.close()
    return
