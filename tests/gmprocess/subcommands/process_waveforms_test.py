import os
import shutil

from gmprocess.apps.gmrecords import GMrecordsApp
from gmprocess.io.asdf.stream_workspace import StreamWorkspace

from gmprocess.utils import constants


def test_process_waveforms():
    try:
        cdir = constants.CONFIG_PATH_TEST
        ddir = constants.TEST_DATA_DIR / "demo_steps" / "process_waveforms"

        # Make a copy of the hdf files
        events = ["ci38457511"]
        for event in events:
            src = ddir / event / "workspace.h5"
            dst = ddir / event / "_workspace.h5"
            shutil.copyfile(src, dst)

        ws = StreamWorkspace(src)
        labels = ws.get_labels()
        assert len(labels) == 1
        assert labels[0] == "unprocessed"
        del ws

        args = {
            "debug": False,
            "quiet": False,
            "event_id": "",
            "textfile": None,
            "overwrite": False,
            "num_processes": 0,
            "label": None,
            "datadir": ddir,
            "confdir": cdir,
            "resume": None,
        }

        app = GMrecordsApp()
        app.load_subcommands()

        subcommand = "process_waveforms"
        step_args = {
            "subcommand": subcommand,
            "func": app.classes[subcommand]["class"],
            "log": None,
        }
        args.update(step_args)
        app.main(**args)

        # Read in HDF file and check that processing tag exists
        ws = StreamWorkspace(src)
        labels = ws.get_labels()
        assert len(labels) == 2
        assert "default" in labels
        del ws

    except Exception as ex:
        raise ex
    finally:
        # Move the hdf files back
        events = ["ci38457511"]
        for event in events:
            dst = os.path.join(ddir, event, "workspace.h5")
            src = os.path.join(ddir, event, "_workspace.h5")
            shutil.move(src, dst)
