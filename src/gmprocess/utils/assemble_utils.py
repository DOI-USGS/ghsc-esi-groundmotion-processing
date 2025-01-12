"""Module for assemble helper functions."""

# stdlib imports
import csv
import logging
import os
from pathlib import Path

from gmprocess.core import scalar_event
from gmprocess.core.streamarray import StreamArray

# local imports
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.io.asdf.rupture import Rupture
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.io.read_directory import directory_to_streams
from gmprocess.utils import constants, rupture_utils
from gmprocess.utils.misc import get_rawdir
from gmprocess.utils.strec import STREC

TIMEFMT2 = "%Y-%m-%dT%H:%M:%S.%f"


FLOAT_PATTERN = r"[-+]?[0-9]*\.?[0-9]+"


def load_event(event_dir):
    event = None
    file_path = event_dir / constants.EVENT_FILE
    if file_path.is_file():
        event = scalar_event.ScalarEvent.from_json(event_dir / constants.EVENT_FILE)
    else:
        logging.warning(f"Could not find {file_path} to get event information.")
    return event


def load_rupture(event, event_dir):
    rupture = None

    file_path = rupture_utils.get_rupture_filename(event_dir)
    if file_path and file_path.is_file():
        rupture = Rupture.from_shakemap(str(file_path), event)
        logging.info("Loaded rupture geometry file.")
    else:
        logging.info("Rupture geometry file not found.")
    return rupture


def load_strec(event_dir):
    file_path = event_dir / constants.STREC_FILE
    return STREC.from_file(file_path)


def assemble(event_id, event, config, directory, gmprocess_version, label):
    """Load data from local directory, turn into Streams.

    Args:
        event_id (str):
            Event id.
        event (ScalarEvent or None):
            Object containing basic event hypocenter, origin time, magnitude.
        config (dict):
            Dictionary with gmprocess configuration information.
        directory (str):
            Path where data already exists. Must be organized in a 'raw'
            directory, within directories with names as the event ids. For
            example, if `directory` is 'proj_dir' and you have data for
            event id 'abc123' then the raw data to be read in should be
            located in `proj_dir/abc123/raw/`.
        gmprocess_version (str):
            Software version for gmprocess.
        label (str):
            Process label, applied to the workspace.add_rupture function

    Returns:
        StreamWorkspace: Contains the event and raw streams.
    """
    event_dir = directory / event_id

    if not event:
        event = load_event(event_dir)
        if not event:
            return
    strec = load_strec(event_dir) if config["strec"]["enabled"] else None
    rupture = load_rupture(event, event_dir)

    # Get raw directory
    raw_dir = get_rawdir(event_dir)
    streams, unprocessed_files, unprocessed_file_errors = directory_to_streams(
        raw_dir, config=config
    )
    # Write errors to a csv file (but not for tests)
    if os.getenv("CALLED_FROM_PYTEST") is None:
        failures_file = Path(raw_dir) / "read_failures.csv"
        colnames = ["File", "Failure"]
        with open(failures_file, "w", newline="") as f:
            writer = csv.writer(f, delimiter=",", quoting=csv.QUOTE_MINIMAL)
            writer.writerow(colnames)
            for ufile, uerror in zip(unprocessed_files, unprocessed_file_errors):
                writer.writerow([ufile, uerror])

    if config["read"]["use_streamcollection"]:
        stream_array = StreamCollection(streams, **config["duplicate"], config=config)
    else:
        stream_array = StreamArray(streams, config=config)

    logging.info(stream_array.describe_string())

    # Create the workspace file and put the unprocessed waveforms in it
    workname = event_dir / constants.WORKSPACE_NAME
    if workname.is_file():
        workname.unlink()

    workspace = StreamWorkspace(workname)
    workspace.add_config(config=config)
    workspace.add_event(event)
    if strec:
        workspace.add_strec(strec, event_id)
    if rupture:
        workspace.add_rupture(rupture, event_id, label=label)
    workspace.add_gmprocess_version(gmprocess_version)
    workspace.add_streams(
        event,
        stream_array,
        label="unprocessed",
        gmprocess_version=gmprocess_version,
    )

    return workspace
