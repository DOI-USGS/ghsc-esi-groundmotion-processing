import shutil
import numpy as np

from gmprocess.apps.gmrecords import GMrecordsApp
from gmprocess.utils import constants
from gmprocess.io.asdf.flatfile import Flatfile
from gmprocess.io.asdf.stream_workspace import StreamWorkspace

EVENTS = ["nc72282711", "nc72282711rupt"]


def test_compute_station_metrics():
    try:
        cdir = constants.CONFIG_PATH_TEST
        ddir = constants.TEST_DATA_DIR / "demo_steps" / "compute_metrics"

        # Make a copy of the hdf files
        for event in EVENTS:
            src = str(ddir / event / "workspace.h5")
            dst = str(ddir / event / "_workspace.h5")
            shutil.copyfile(src, dst)

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

        subcommand = "compute_station_metrics"
        step_args = {
            "subcommand": subcommand,
            "func": app.classes[subcommand]["class"],
            "log": None,
        }
        args.update(step_args)
        app.main(**args)

        subcommand = "compute_waveform_metrics"
        step_args = {
            "subcommand": subcommand,
            "func": app.classes[subcommand]["class"],
            "log": None,
        }
        args.update(step_args)
        app.main(**args)

        # Test resulting metrics with rupture file
        ws_file = str(ddir / EVENTS[1] / "workspace.h5")
        rupt_ws = StreamWorkspace(ws_file)

        # check that workspace has a rupture file
        assert isinstance(rupt_ws.get_rupture(EVENTS[1]), dict)

        ff_rupt = Flatfile(rupt_ws)
        _, imc_tables_rupt, _ = ff_rupt.get_tables()
        rotd_rupt = imc_tables_rupt["RotD(percentile=50.0)"]

        np.testing.assert_allclose(
            rotd_rupt.EpicentralDistance.iloc[0],
            84.27,
        )
        np.testing.assert_allclose(
            rotd_rupt.RuptureDistance.iloc[0],
            84.82,
        )

        np.testing.assert_allclose(
            rotd_rupt["SA(T=0.3000, D=0.050)"].iloc[0],
            4.5235322,
        )

        # Test resulting metrics without rupture file
        ws_file = str(ddir / EVENTS[0] / "workspace.h5")
        test_ws = StreamWorkspace(ws_file)

        # check that workspace has a rupture file
        assert test_ws.get_rupture(EVENTS[0]) is None

        ff = Flatfile(test_ws)
        _, imc_tables, _ = ff.get_tables()
        rotd = imc_tables["RotD(percentile=50.0)"]

        np.testing.assert_allclose(
            rotd.EpicentralDistance.iloc[0],
            84.27,
        )
        np.testing.assert_allclose(
            rotd.RuptureDistance.iloc[0],
            81.08,
        )
        np.testing.assert_allclose(
            rotd["SA(T=0.3000, D=0.050)"].iloc[0],
            4.5235322,
        )

    except Exception as ex:
        raise ex
    finally:
        # Move the hdf files back
        for event in EVENTS:
            dst = str(ddir / event / "workspace.h5")
            src = str(ddir / event / "_workspace.h5")
            shutil.move(src, dst)
