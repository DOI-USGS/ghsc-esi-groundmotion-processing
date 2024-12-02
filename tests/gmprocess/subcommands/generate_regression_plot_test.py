import os
import shutil

from gmprocess.apps.gmrecords import GMrecordsApp
from gmprocess.utils import constants


def test_export_regression_plot():
    try:
        cdir = str(constants.CONFIG_PATH_TEST)
        ddir = str(constants.TEST_DATA_DIR / "demo_steps" / "exports")

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

        subcommand = "export_metric_tables"
        step_args = {
            "subcommand": subcommand,
            "func": app.classes[subcommand]["class"],
            "log": None,
            "skip_download": True,
        }
        args.update(step_args)
        app.main(**args)

        subcommand = "generate_regression_plot"
        step_args = {
            "subcommand": subcommand,
            "func": app.classes[subcommand]["class"],
            "log": None,
        }
        args.update(step_args)
        app.main(**args)

        # Check that files were created
        count = 0
        pattern = "regression_"
        for root, _, files in os.walk(ddir):
            for file in files:
                if pattern in file:
                    count += 1
        assert count == 1

    except Exception as ex:
        raise ex
    finally:
        shutil.rmtree(str(constants.CONFIG_PATH_TEST), ignore_errors=True)
        # Remove created files
        patterns = [
            "_metrics_",
            "_events.",
            "_snr",
            "_fit_spectra_parameters",
            "regression_",
        ]
        for root, _, files in os.walk(ddir):
            for file in files:
                for pattern in patterns:
                    if pattern in file:
                        os.remove(os.path.join(root, file))
