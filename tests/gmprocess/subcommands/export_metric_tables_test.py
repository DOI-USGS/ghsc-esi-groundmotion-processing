import os
import shutil

import numpy as np
import pandas as pd

from gmprocess.apps.gmrecords import GMrecordsApp
from gmprocess.utils import constants


def test_export_metric_tables():
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
        }
        args.update(step_args)
        app.main(**args)

        # Check that output tables were created
        count = 0
        pattern = "_metrics_"
        for root, _, files in os.walk(ddir):
            for file in files:
                if pattern in file:
                    count += 1
        assert count == 12

        h1df = pd.read_csv(
            os.path.join(ddir, "None_default_metrics_channels(component=h1).csv")
        )
        for i in range(h1df.shape[0]):
            assert h1df["EarthquakeId"][i] == "ci38457511"
        np.testing.assert_allclose(
            h1df["EarthquakeLatitude"],
            np.full_like(h1df["EarthquakeLatitude"], 35.7695),
        )
        np.testing.assert_allclose(
            h1df["EarthquakeLongitude"],
            np.full_like(h1df["EarthquakeLongitude"], -117.59933),
        )
        np.testing.assert_allclose(
            h1df["EarthquakeDepth"], np.full_like(h1df["EarthquakeDepth"], 8.0)
        )
        np.testing.assert_allclose(h1df[h1df["StationCode"] == "CCC"]["PGA"], 48.013271)

        qmdf = pd.read_csv(
            os.path.join(ddir, "None_default_metrics_quadraticmean().csv")
        )

        np.testing.assert_allclose(
            qmdf[qmdf["StationCode"] == "CCC"]["FAS(f=5.62341325, B=20.0)"],
            62.856018,
        )

    except Exception as ex:
        raise ex
    finally:
        shutil.rmtree(str(constants.CONFIG_PATH_TEST), ignore_errors=True)
        # Remove created files
        patterns = ["_metrics_", "_events.", "_fit_spectra_parameters", "_snr"]
        for root, _, files in os.walk(ddir):
            for file in files:
                for pattern in patterns:
                    if pattern in file:
                        os.remove(os.path.join(root, file))
