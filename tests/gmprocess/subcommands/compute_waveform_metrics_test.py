import io
import shutil
from gmprocess.utils import constants

EVENTS = ["ci38457511", "ci38457511_rupt"]


def test_compute_waveform_metrics(script_runner):
    try:
        # Need to create profile first.
        cdir = constants.CONFIG_PATH_TEST
        ddir = constants.TEST_DATA_DIR / "demo_steps" / "compute_metrics"

        # Make a copy of the hdf files
        for event in EVENTS:
            src = str(ddir / event / "workspace.h5")
            dst = str(ddir / event / "_workspace.h5")
            shutil.copyfile(src, dst)

        setup_inputs = io.StringIO(f"test\n{cdir}\n{ddir}\nname\ntest@email.com\n")
        ret = script_runner.run("gmrecords", "projects", "-c", stdin=setup_inputs)
        setup_inputs.close()
        print(ret)

        assert ret.success

        ret = script_runner.run("gmrecords", "compute_waveform_metrics")
        assert ret.success

        assert "Adding waveform metrics to workspace files with" in ret.stderr
        assert "Calculating waveform metrics for CI.LRL.HN" in ret.stderr

    except Exception as ex:
        raise ex
    finally:
        shutil.rmtree(str(constants.CONFIG_PATH_TEST), ignore_errors=True)
        # Move the hdf files back
        for event in EVENTS:
            dst = str(ddir / event / "workspace.h5")
            src = str(ddir / event / "_workspace.h5")
            shutil.move(src, dst)
