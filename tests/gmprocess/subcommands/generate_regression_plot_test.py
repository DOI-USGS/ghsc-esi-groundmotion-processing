import io
import os
import shutil

from gmprocess.utils import constants


def test_export_regression_plot(script_runner):
    try:
        # Need to create profile first.
        cdir = str(constants.CONFIG_PATH_TEST)
        ddir = str(constants.TEST_DATA_DIR / "demo_steps" / "exports")

        setup_inputs = io.StringIO(f"test\n{cdir}\n{ddir}\nname\ntest@email.com\n")
        ret1 = script_runner.run("gmrecords", "projects", "-c", stdin=setup_inputs)
        setup_inputs.close()
        assert ret1.success

        ret2 = script_runner.run("gmrecords", "export_metric_tables")
        assert ret2.success

        ret3 = script_runner.run("gmrecords", "regression")
        assert ret3.success

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
