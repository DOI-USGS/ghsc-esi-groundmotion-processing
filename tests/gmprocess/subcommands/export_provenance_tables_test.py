import os
import shutil

import pandas as pd

from gmprocess.apps.gmrecords import GMrecordsApp
from gmprocess.utils import constants


def test_export_provenance_tables():
    try:
        cdir = constants.CONFIG_PATH_TEST
        ddir = constants.TEST_DATA_DIR / "demo_steps" / "exports"

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

        subcommand = "export_provenance_tables"
        step_args = {
            "subcommand": subcommand,
            "func": app.classes[subcommand]["class"],
            "log": None,
        }
        args.update(step_args)
        app.main(**args)

        pfile = ddir / "ci38457511" / "None_default_provenance.csv"
        assert pfile.is_file()

        ptable = pd.read_csv(pfile)
        assert ptable.shape == (216, 4)

    except Exception as ex:
        raise ex
    finally:
        shutil.rmtree(str(constants.CONFIG_PATH_TEST), ignore_errors=True)
        # Remove created files
        pattern = "_provenance"
        for root, _, files in os.walk(ddir):
            for file in files:
                if pattern in file:
                    os.remove(os.path.join(root, file))
