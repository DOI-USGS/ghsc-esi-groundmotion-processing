import os

from gmprocess.apps.gmrecords import GMrecordsApp
from gmprocess.utils import constants


def test_generate_station_maps():
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

        subcommand = "generate_station_maps"
        step_args = {
            "subcommand": subcommand,
            "func": app.classes[subcommand]["class"],
            "log": None,
        }
        args.update(step_args)
        app.main(**args)

        map_file = ddir / "ci38457511" / "stations_map.html"
        assert map_file.is_file()

    except Exception as ex:
        raise ex
    finally:
        # Remove workspace and image files
        pattern = [
            ".png",
            ".csv",
            ".html",
            "_dat.json",
            "_groundmotion_packet.json",
        ]
        for root, _, files in os.walk(ddir):
            for file in files:
                if any(file.endswith(ext) for ext in pattern):
                    os.remove(os.path.join(root, file))
