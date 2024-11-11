"""Module to define fixutres for the io package."""

import pathlib

import pytest

from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.utils import constants
from gmprocess.core import scalar_event
from gmprocess.utils.strec import STREC
from gmprocess.utils.config import get_config

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


@pytest.fixture(scope="package")
def config():
    """Get config."""
    return dict(get_config())


@pytest.fixture(scope="package")
def load_ci38457511_demo_export():
    """Load the workspace file for the ci38457511 demo export test."""
    ddir = constants.TEST_DATA_DIR / "demo_steps" / "exports" / "ci38457511"
    ws_file = ddir / "workspace.h5"
    ws = StreamWorkspace(ws_file)
    return ws


@pytest.fixture(scope="package")
def load_data_usb000syza():
    """Load data for event usb000syza.

    Returns:
        tuple: (StreamCollection, Event, strec).
    """
    event_dir = constants.TEST_DATA_DIR / "knet" / "usb000syza"
    sc = StreamCollection.from_directory(event_dir)
    event = scalar_event.ScalarEvent.from_json(event_dir / constants.EVENT_FILE)
    strec = STREC.from_file(event_dir / constants.STREC_FILE)
    return sc, event, strec


@pytest.fixture(scope="package")
def load_data_us1000778i():
    """Load data for event us1000778i.

    Returns:
        tuple: (StreamCollection, Event).
    """
    event_dir = constants.TEST_DATA_DIR / "geonet" / "us1000778i"
    sc = StreamCollection.from_directory(event_dir)
    event = scalar_event.ScalarEvent.from_json(event_dir / constants.EVENT_FILE)
    return sc, event


@pytest.fixture(scope="package")
def configure_strec():
    """Fixture to configure STREC.

    Returns: config.
    """
    config_data = None
    if constants.STREC_CONFIG_PATH.exists():
        with open(constants.STREC_CONFIG_PATH, "rt", encoding="utf-8") as f:
            config_data = f.read()
    else:
        constants.STREC_CONFIG_PATH.parent.mkdir()
    # where is the strec test data folder
    test_strec_dir = (pathlib.Path(".") / "tests" / "data" / "strec").resolve()
    strec_config_str = TEST_STREC_CONFIG.replace(
        "[TEST_STREC_DIR]", str(test_strec_dir)
    )
    with open(constants.STREC_CONFIG_PATH, "wt", encoding="utf-8") as f:
        f.write(strec_config_str)
    return config_data
