import io
import os
import shutil
import json

from gmprocess.utils import constants
from gmprocess.utils import tests_utils


def test_autoshakemap(script_runner):
    EVENT_ID = "ci38457511"
    STATION_IDS = (
        "CI.CCC",
        "CI.CLC",
        "CI.TOW2",
    )

    try:
        # Need to create profile first.
        cdir = constants.CONFIG_PATH_TEST
        ddir = constants.TEST_DATA_DIR / "demo"
        setup_inputs = io.StringIO(
            f"test\n{str(cdir)}\n{str(ddir)}\nname\ntest@email.com\n"
        )
        ret = script_runner.run("gmrecords", "projects", "-c", stdin=setup_inputs)
        setup_inputs.close()
        assert ret.success

        ret = script_runner.run(
            "gmrecords", "-e", EVENT_ID, "autoshakemap", "--skip-download"
        )
        assert ret.success

        event_dir = ddir / EVENT_ID

        filename = event_dir / f"{EVENT_ID}_metrics.json"
        with open(filename, encoding="utf-8") as fin:
            metrics = json.load(fin)
            assert metrics["software"]["name"] == "gmprocess"
            assert metrics["event"]["id"] == EVENT_ID
            assert len(metrics["features"]) == len(STATION_IDS)
            for i_station, station_id in enumerate(STATION_IDS):
                properties = metrics["features"][i_station]["properties"]
                network_code, station_code = station_id.split(".")
                assert properties["network_code"] == network_code
                assert properties["station_code"] == station_code

        filename = event_dir / f"{EVENT_ID}_groundmotions_dat.json"
        with open(filename, encoding="utf-8") as fin:
            data = json.load(fin)
            assert len(data["features"]) == len(STATION_IDS)
            for i_station, station_id in enumerate(STATION_IDS):
                feature = data["features"][i_station]
                assert feature["id"] == station_id

    except Exception as ex:
        raise ex
    finally:
        shutil.rmtree(constants.CONFIG_PATH_TEST)
        # Remove workspace and image files
        pattern = ["workspace.h5", ".png", ".csv", "_dat.json", "_metrics.json"]
        for root, _, files in os.walk(ddir):
            for file in files:
                if any(file.endswith(ext) for ext in pattern):
                    os.remove(os.path.join(root, file))
