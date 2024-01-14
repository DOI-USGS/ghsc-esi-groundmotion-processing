from pathlib import Path

import numpy as np
import pytest

from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.utils import constants
from gmprocess.utils.config import update_config
from gmprocess.waveform_processing.processing import process_streams
from gmprocess.utils.test_utils import vcr


def assert_cmp_with_nans(d1, d2):
    for key, v1 in d1.items():
        if key not in d2:
            raise AssertionError(f"{key} not in both compared dictionaries.")
        v2 = d2[key]
        if isinstance(v1, str):
            assert v1 == v2
        else:
            np.testing.assert_allclose(v1, v2, atol=1e-2)


def test_stream_open_close():
    """Test open and closing StreamWorkspace."""
    filename = constants.TEST_DATA_DIR / "empty_workspace.h5"
    filename.unlink(missing_ok=True)
    ws = StreamWorkspace.create(filename)
    ws.close()

    ws = StreamWorkspace.open(filename)
    ws.close()
    filename.unlink()


@vcr.use_cassette()
def test_stream_workspace_methods(load_data_usb000syza, configure_strec, tmp_path):
    """Test for StreamWorkspace class."""
    try:
        event_id = "usb000syza"
        _, event, strec = load_data_usb000syza

        ws = StreamWorkspace.create(tmp_path / "workspace.h5")

        # make sure that strec is configured
        existing_config_data = configure_strec
        try:
            ws.add_config()
            ws.add_event(event)
            ws.add_strec(strec, event_id)
            outevent = ws.get_event(event_id)
            strec_params = ws.get_strec(event_id)
            cmp_params = {
                "CompositeVariability": np.nan,
                "DistanceToActive": 416.1843055109172,
                "DistanceToBackarc": 0.0,
                "DistanceToContinental": 0.0,
                "DistanceToOceanic": 230.7525263607655,
                "DistanceToStable": 652.6654705874242,
                "DistanceToSubduction": 0.0,
                "DistanceToVolcanic": 3716.302616840036,
                "FocalMechanism": "RS",
                "KaganAngle": 31.006964460128096,
                "NComposite": 0,
                "Oceanic": False,
                "ProbabilityActive": 0.0,
                "ProbabilityActiveDeep": 0.0,
                "ProbabilityActiveShallow": 0.0,
                "ProbabilityStable": 0.0,
                "ProbabilityStableShallow": 0.0,
                "ProbabilitySubduction": 1.0,
                "ProbabilitySubductionCrustal": 0.8652238784260651,
                "ProbabilitySubductionInterface": 0.13477612157393487,
                "ProbabilitySubductionIntraslab": 0.0,
                "ProbabilityVolcanic": 0.0,
                "ProbabilityVolcanicShallow": 0.0,
                "SlabModelDepth": 138.8086700439453,
                "SlabModelDepthUncertainty": 17.509645462036133,
                "SlabModelDip": 31.167997360229492,
                "SlabModelMaximumDepth": 47,
                "SlabModelRegion": "Ryukyu",
                "SlabModelStrike": 240.8999481201172,
                "TectonicRegion": "Subduction",
                "TensorSource": "us",
                "TensorType": "Mww",
            }

            assert_cmp_with_nans(strec_params, cmp_params)
        finally:
            if existing_config_data is not None:
                with open(constants.STREC_CONFIG_PATH, "wt", encoding="utf-8") as f:
                    f.write(existing_config_data)
        ws.close()

        with pytest.raises(OSError):
            StreamWorkspace.open(tmp_path / "nonexistance_file.h5")

    except BaseException as e:
        raise e


def test_stream_workspace(load_data_usb000syza, tmp_path, config):
    config["metrics"]["output_imcs"] = ["channels"]
    raw_streams, event, strec = load_data_usb000syza
    config = update_config(constants.TEST_DATA_DIR / "config_min_freq_0p2.yml", config)
    newconfig = config.copy()
    newconfig["processing"].append(
        {"nnet_qa": {"acceptance_threshold": 0.5, "model_name": "CantWell"}}
    )
    processed_streams = process_streams(raw_streams.copy(), event, config=newconfig)

    try:
        tfile = tmp_path / "test.hdf"
        workspace = StreamWorkspace(tfile)
        workspace.add_config(config=config)
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


def test_stream_workspace_ucla_review():
    reviewed_workspace = constants.TEST_DATA_DIR / "ucla_review" / "workspace.h5"
    ws = StreamWorkspace.open(reviewed_workspace)
    st = ws.get_streams("se60324281")
    assert len(st) == 8
