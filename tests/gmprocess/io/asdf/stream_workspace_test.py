#!/usr/bin/env python

import os
import shutil
import tempfile
from pathlib import Path

import numpy as np
import pytest
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.utils import constants
from gmprocess.utils.config import get_config, update_config
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.waveform_processing.processing import process_streams

CONFIG = get_config()

TEST_STREC_CONFIG = """[DATA]
folder = [TEST_STREC_DIR]
slabfolder = [TEST_STREC_DIR]/slabs
dbfile = [TEST_STREC_DIR]/moment_tensors.db
longest_axis = 6161.22354153315

[CONSTANTS]
minradial_disthist = 0.01
maxradial_disthist = 1.0
minradial_distcomp = 0.5
maxradial_distcomp = 1.0
step_distcomp = 0.1
depth_rangecomp = 10
minno_comp = 3
default_szdip = 17
dstrike_interf = 30
ddip_interf = 30
dlambda = 60
ddepth_interf = 20
ddepth_intra = 10"""

STREC_CONFIG_PATH = Path.home() / ".strec" / "config.ini"


def assert_cmp_with_nans(d1, d2):
    for key, v1 in d1.items():
        if key not in d2:
            raise AssertionError(f"{key} not in both compared dictionaries.")
        v2 = d2[key]
        if isinstance(v1, str):
            assert v1 == v2
        else:
            np.testing.assert_allclose(v1, v2, atol=1e-2)


def configure_strec():
    config_data = None
    if STREC_CONFIG_PATH.exists():
        with open(STREC_CONFIG_PATH, "rt") as f:
            config_data = f.read()
    else:
        STREC_CONFIG_PATH.parent.mkdir()
    # where is the strec test data folder
    test_strec_dir = (Path(".") / "tests" / "data" / "strec").resolve()
    strec_config_str = TEST_STREC_CONFIG.replace(
        "[TEST_STREC_DIR]", str(test_strec_dir)
    )
    with open(STREC_CONFIG_PATH, "wt") as f:
        print(f"***Writing new config to {STREC_CONFIG_PATH}")
        f.write(strec_config_str)
    return config_data


def test_stream_workspace_methods():
    tdir = Path(tempfile.mkdtemp())
    try:
        eventid = "usb000syza"
        _, event = read_data_dir("knet", eventid, "*")

        ws = StreamWorkspace.create(tdir / "workspace.h5")

        # make sure that strec is configured
        existing_config_data = configure_strec()
        try:
            ws.add_event(event)
            outevent = ws.get_event(eventid)
            strec_params = ws.get_strec(outevent)
            cmp_params = {
                "TectonicRegion": "Subduction",
                "FocalMechanism": "RS",
                "TensorType": "Mww",
                "TensorSource": "us",
                "KaganAngle": 31.006964460128113,
                "CompositeVariability": np.nan,
                "NComposite": 0,
                "DistanceToStable": 652.6654705874242,
                "DistanceToActive": 416.1843055109172,
                "DistanceToSubduction": 0.0,
                "DistanceToHotSpot": 3716.302616840036,
                "Oceanic": False,
                "DistanceToOceanic": 230.75252636076507,
                "DistanceToContinental": 0.0,
                "SlabModelRegion": "Ryukyu",
                "SlabModelDepth": 138.8086700439453,
                "SlabModelDepthUncertainty": 17.509645462036133,
                "SlabModelDip": 31.167997360229492,
                "SlabModelStrike": 240.8999481201172,
                "SlabModelMaximumDepth": 47,
                "ProbabilityActive": 0.0,
                "ProbabilityStable": 0.0,
                "ProbabilitySubduction": 1.0,
                "ProbabilityVolcanic": 0.0,
                "ProbabilitySubductionCrustal": 0.8652238784260652,
                "ProbabilitySubductionInterface": 0.1347761215739348,
                "ProbabilitySubductionIntraslab": 0.0,
                "ProbabilityActiveShallow": 0.0,
                "ProbabilityStableShallow": 0.0,
                "ProbabilityVolcanicShallow": 0.0,
                "ProbabilityActiveDeep": 0.0,
                "DistanceToBackarc": 0.0,
            }
            assert_cmp_with_nans(strec_params, cmp_params)
        finally:
            if existing_config_data is not None:
                with open(STREC_CONFIG_PATH, "wt") as f:
                    f.write(existing_config_data)
        ws.close()

        with pytest.raises(OSError):
            StreamWorkspace.open(tdir / "nonexistance_file.h5")

    except BaseException as e:
        raise e
    finally:
        shutil.rmtree(tdir, ignore_errors=True)


def test_stream_workspace():
    CONFIG["metrics"]["output_imcs"] = ["channels"]
    eventid = "usb000syza"
    datafiles, event = read_data_dir("knet", eventid, "*")
    datadir = Path(datafiles[0]).parent
    raw_streams = StreamCollection.from_directory(datadir)
    config = update_config(datadir / "config_min_freq_0p2.yml", CONFIG)
    newconfig = config.copy()
    newconfig["processing"].append(
        {"nnet_qa": {"acceptance_threshold": 0.5, "model_name": "CantWell"}}
    )
    processed_streams = process_streams(raw_streams.copy(), event, config=newconfig)

    tdir = Path(tempfile.mkdtemp())
    try:
        tfile = tdir / "test.hdf"
        workspace = StreamWorkspace(tfile)
        workspace.add_event(event)
        workspace.add_streams(event, raw_streams, label="raw")
        workspace.add_streams(event, processed_streams, label="processed")
        assert workspace.__repr__() == "Events: 1 Stations: 2 Streams: 4"
        lab_df = workspace.summarize_labels()
        assert lab_df.shape == (2, 6)
        inv = workspace.get_inventory()
        assert inv.source == (
            "Japan National Research Institute for Earth Science and Disaster "
            "Resilience"
        )
        workspace.close()
    except Exception as e:
        raise (e)
    finally:
        shutil.rmtree(tdir, ignore_errors=True)


def test_stream_workspace_ucla_review():
    reviewed_workspace = constants.TEST_DATA_DIR / "ucla_review" / "workspace.h5"
    ws = StreamWorkspace.open(reviewed_workspace)
    st = ws.get_streams("se60324281")
    assert len(st) == 8


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_stream_workspace_methods()
    test_stream_workspace()
    test_stream_workspace_ucla_review()
