import io
import os
import shutil

from gmprocess.utils import constants


def test_generate_station_maps(script_runner):
    try:
        # Need to create profile first.
        cdir = constants.CONFIG_PATH_TEST
        ddir = constants.TEST_DATA_DIR / "demo_steps" / "exports"
        # backup the workspace file and put it back later
        workpsace_orig = str(ddir / "ci38457511" / "workspace.h5")
        workpsace_backup = str(ddir / "ci38457511" / ".workspace.h5_backup")
        shutil.copyfile(workpsace_orig, workpsace_backup)
        setup_inputs = io.StringIO(
            f"test\n{str(cdir)}\n{str(ddir)}\nname\ntest@email.com\n"
        )
        ret = script_runner.run("gmrecords", "projects", "-c", stdin=setup_inputs)
        setup_inputs.close()
        assert ret.success

        ret = script_runner.run("gmrecords", "-e", "ci38457511", "report")
        assert ret.success

        ret = script_runner.run("gmrecords", "-e", "ci38457511", "clean", "--all")
        assert ret.success

    except Exception as ex:
        raise ex
    finally:
        shutil.rmtree(constants.CONFIG_PATH_TEST, ignore_errors=True)
        # Remove workspace and image files
        pattern = [
            ".png",
            ".csv",
            ".html",
            "_dat.json",
            "_metrics.json",
        ]
        for root, _, files in os.walk(ddir):
            for file in files:
                if any(file.endswith(ext) for ext in pattern):
                    os.remove(os.path.join(root, file))
        shutil.move(workpsace_backup, workpsace_orig)
