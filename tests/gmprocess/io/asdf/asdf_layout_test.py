# stdlib imports
import os
import shutil
import tempfile

# third party imports
import h5py

from stream_workspace_test import STREC_CONFIG_PATH, configure_strec

from gmprocess.io.asdf.core import write_asdf
from gmprocess.io.asdf.stream_workspace import StreamWorkspace

from gmprocess.io.read import read_data
from gmprocess.io.asdf.waveform_metrics_xml import WaveformMetricsXML
from gmprocess.io.asdf.station_metrics_xml import StationMetricsXML
from gmprocess.utils.config import get_config, update_config
from gmprocess.utils.constants import TEST_DATA_DIR
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.metrics.waveform_metric_collection import WaveformMetricCollection
from gmprocess.metrics.station_metric_collection import StationMetricCollection
from gmprocess.waveform_processing.processing import process_streams


CONFIG = get_config()


def generate_workspace():
    """Generate simple HDF5 with ASDF layout for testing."""
    EVENTID = "us1000778i"
    LABEL = "ptest"
    datafiles, event = read_data_dir("geonet", EVENTID, "*.V1A")

    tdir = tempfile.mkdtemp()
    tfilename = os.path.join(tdir, "workspace.h5")

    raw_data = []
    for dfile in datafiles:
        raw_data += read_data(dfile)

    existing_config_data = configure_strec()
    try:
        write_asdf(tfilename, raw_data, event, label="unprocessed")
        del raw_data

        config = update_config(str(TEST_DATA_DIR / "config_min_freq_0p2.yml"), CONFIG)

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
            with open(STREC_CONFIG_PATH, "wt") as f:
                f.write(existing_config_data)

    return tfilename


def setup_module(module):
    setup_module.tfilename = generate_workspace()
    return


def teardown_module(module):
    tdir = os.path.split(setup_module.tfilename)[0]
    shutil.rmtree(tdir, ignore_errors=True)
    return


def test_layout():
    LAYOUT_FILENAME = "asdf_layout.txt"

    tfilename = setup_module.tfilename
    h5 = h5py.File(tfilename, "r")

    testroot = str(TEST_DATA_DIR / "asdf")
    layout_abspath = os.path.join(testroot, LAYOUT_FILENAME)
    with open(layout_abspath, "r", encoding="utf-8") as fin:
        lines = fin.readlines()
        for line in lines:
            assert line.strip() in h5
    h5.close()
    return
