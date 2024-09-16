import io
import shutil
import numpy as np

from gmprocess.utils import constants
from gmprocess.io.asdf.flatfile import Flatfile
from gmprocess.io.asdf.stream_workspace import StreamWorkspace

EVENTS = ["ci38457511", "ci38457511_rupt"]


def test_compute_station_metrics(script_runner):
    try:
        # Need to create profile first.
        cdir = constants.CONFIG_PATH_TEST
        ddir = constants.TEST_DATA_DIR / "demo_steps" / "compute_metrics"

        # Make a copy of the hdf files
        for event in EVENTS:
            src = str(ddir / event / "workspace.h5")
            dst = str(ddir / event / "_workspace.h5")
            shutil.copyfile(src, dst)

        setup_inputs = io.StringIO(
            f"test\n{str(cdir)}\n{str(ddir)}\nname\ntest@email.com\n"
        )
        ret = script_runner.run("gmrecords", "projects", "-c", stdin=setup_inputs)
        setup_inputs.close()
        assert ret.success

        ret = script_runner.run("gmrecords", "compute_station_metrics")
        assert ret.success

        # No new files created, check stderr
        assert "Added station metrics to workspace files with" in ret.stderr
        assert "Computing station metrics" in ret.stderr

        # Test that station metrics has computed the expected distances
        test_ws = StreamWorkspace(dst)
        ff = Flatfile(test_ws)
        _, imc_tables, _ = ff.get_tables()
        np.testing.assert_allclose(
            imc_tables["RotD(percentile=50.0)"].EpicentralDistance.iloc[0],
            33.03,
            atol=1e-7,
        )
        np.testing.assert_allclose(
            imc_tables["RotD(percentile=50.0)"].RuptureDistance.iloc[0],
            26.25,
            atol=1e-7,
        )
        np.testing.assert_allclose(
            imc_tables["RotD(percentile=50.0)"].EpicentralDistance.iloc[2],
            14.51,
            atol=1e-7,
        )
        np.testing.assert_allclose(
            imc_tables["RotD(percentile=50.0)"].RuptureDistance.iloc[2],
            11.22,
            atol=1e-7,
        )

        # ret = script_runner.run("gmrecords", "-o", "compute_station_metrics")
        # assert ret.success

    except Exception as ex:
        raise ex
    finally:
        shutil.rmtree(constants.CONFIG_PATH_TEST, ignore_errors=True)
        # Move the hdf files back
        for event in EVENTS:
            dst = str(ddir / event / "workspace.h5")
            src = str(ddir / event / "_workspace.h5")
            shutil.move(src, dst)
