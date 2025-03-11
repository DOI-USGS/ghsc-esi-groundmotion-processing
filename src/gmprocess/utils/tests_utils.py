"""Module for utilities related to unit tests."""

import os
import h5py
import vcr as vcrpy

from gmprocess.utils import constants
from gmprocess.core import scalar_event

vcr = vcrpy.VCR(
    path_transformer=vcrpy.VCR.ensure_suffix(".yaml"),
    cassette_library_dir=str(constants.TEST_DATA_DIR / "vcr_cassettes"),
    record_mode="once",
    match_on=["uri"],
)


def read_data_dir(file_format, eventid, files=None):
    """Read desired data files and event dictionary from test directory.

    Args:
        file_format (str):
            Name of desired data format (smc, usc, etc.)
        eventid (str):
            ComCat or other event ID (should exist as a folder)
        files (variable):
            This is either:
                - None This is a flag to retrieve all of the files for an
                  event.
                - regex A regex string that glob can handle (*.dat, AO*.*,
                  etc.)
                - list List of specific files that should be returned.

    Returns:
        tuple:
            - List of data files.
            - Event dictionary.
    """
    eventdir = constants.TEST_DATA_DIR / file_format / eventid
    if not eventdir.is_dir():
        return (None, None)
    datafiles = []
    if files is None:
        allfiles = os.listdir(eventdir)
        allfiles.remove("event.json")
        for dfile in allfiles:
            datafile = eventdir / dfile
            datafiles.append(datafile)
    elif isinstance(files, str):
        # files is a regular expression
        datafiles = list(eventdir.glob(files))
    else:
        # files is a list of filenames
        for tfile in files:
            fullfile = eventdir / tfile
            if fullfile.is_file():
                datafiles.append(fullfile)

    jsonfile = eventdir / "event.json"
    event = None
    if jsonfile.is_file():
        event = scalar_event.ScalarEvent.from_json(jsonfile)

    return (datafiles, event)


def check_workspace(filename, hierarchy):
    """Check workspace hierarchy to make sure it contains all expected items.

    Args:
        filename (pathlib.Path):
            Filename of ASDF workspace.
        hierarchy (tuple):
            Tuple of names of items in workspace (matches h5dump -n).
    """

    def tracker(name):
        tracker.items.append(name)

    assert filename.is_file()
    with h5py.File(filename) as h5:
        tracker.items = []
        h5.visit(tracker)
        assert sorted(tuple(tracker.items)) == sorted(hierarchy)
