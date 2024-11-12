import io
import os
import shutil
import copy

import numpy as np
import pandas as pd

from gmprocess.utils import constants


def test_export_metric_tables(script_runner, config):
    conf = copy.deepcopy(config)

    try:
        # Need to create profile first.
        cdir = str(constants.CONFIG_PATH_TEST)
        ddir = str(constants.TEST_DATA_DIR / "demo_steps" / "exports")

        setup_inputs = io.StringIO(f"test\n{cdir}\n{ddir}\nname\ntest@email.com\n")
        ret = script_runner.run("gmrecords", "projects", "-c", stdin=setup_inputs)
        setup_inputs.close()
        assert ret.success

        conf["metrics"]["components_and_types"]["quadratic_mean"] = "fas"

        ret = script_runner.run("gmrecords", "mtables")
        assert ret.success

        # Check that output tables were created
        count = 0
        pattern = "_metrics_"
        for root, _, files in os.walk(ddir):
            for file in files:
                if pattern in file:
                    count += 1
        assert count == 12
        # Check contents of one file
        h1df = pd.read_csv(
            os.path.join(ddir, "test_default_metrics_channels(component=h1).csv")
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
        np.testing.assert_allclose(
            h1df["EarthquakeDepth"], np.full_like(h1df["EarthquakeDepth"], 8.0)
        )

        # Turn off default metrics
        conf["metrics"]["components_and_types"]["channels"] = ""
        ret = script_runner.run("gmrecords", "mtables")
        assert ret.success

        qmdf = pd.read_csv(
            os.path.join(ddir, "test_default_metrics_quadraticmean().csv")
        )
        np.testing.assert_allclose(
            qmdf["FAS(f=5.62341325, B=20.0)"].iloc[0],
            63.022771,
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
