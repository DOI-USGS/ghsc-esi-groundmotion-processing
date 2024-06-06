import io
import os
import shutil
import json

from gmprocess.utils import constants


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

        filename = event_dir / f"{EVENT_ID}_groundmotion_packet.json"
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
        shutil.rmtree(constants.CONFIG_PATH_TEST)
        # Remove workspace and image files
        pattern = ["workspace.h5", ".png", ".csv", "_dat.json", "_metrics.json"]
        for root, _, files in os.walk(ddir):
            for file in files:
                if any(file.endswith(ext) for ext in pattern):
                    os.remove(os.path.join(root, file))
