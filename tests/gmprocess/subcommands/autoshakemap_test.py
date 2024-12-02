import os
import json

from gmprocess.apps.gmrecords import GMrecordsApp
from gmprocess.utils import constants


def test_autoshakemap():
    EVENT_ID = "ci38457511"
    STATION_IDS = (
        "CI.CCC",
        "CI.CLC",
        "CI.TOW2",
    )

    cdir = constants.CONFIG_PATH_TEST
    ddir = constants.TEST_DATA_DIR / "demo"
    event_dir = ddir / EVENT_ID
    filename = event_dir / f"{EVENT_ID}_groundmotion_packet.json"
    try:
        args = {
            "debug": False,
            "quiet": False,
            "event_id": EVENT_ID,
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

        subcommand = "autoshakemap"
        step_args = {
            "subcommand": subcommand,
            "func": app.classes[subcommand]["class"],
            "log": None,
            "skip_download": True,
        }
        args.update(step_args)
        app.main(**args)

        with open(filename, encoding="utf-8") as fin:
            data = json.load(fin)
            assert len(data["features"]) == len(STATION_IDS)
            for i_station, station_id in enumerate(STATION_IDS):
                fprops = data["features"][i_station]["properties"]
                assert (
                    f"{fprops['network_code']}.{fprops['station_code']}" == station_id
                )
    except Exception as ex:
        raise ex
    finally:
        filename.unlink(missing_ok=True)
        # Remove workspace and image files
        pattern = [
            "workspace.h5",
            ".png",
            ".csv",
            "_dat.json",
            "_groundmotion_packet.json",
        ]
        for root, _, files in os.walk(ddir):
            for file in files:
                if any(file.endswith(ext) for ext in pattern):
                    os.remove(os.path.join(root, file))
