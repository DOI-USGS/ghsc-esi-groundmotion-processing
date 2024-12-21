import os

from gmprocess.apps.gmrecords import GMrecordsApp
from gmprocess.utils import constants, tests_utils


def test_assemble_event_list():
    try:
        cdir = constants.CONFIG_PATH_TEST
        ddir = constants.TEST_DATA_DIR / "kiknet"

        EVENT_IDS = "usp000a1b0, usp000hzq8"

        ws_files = [
            ddir / "usp000a1b0" / "workspace.h5",
            ddir / "usp000hzq8" / "workspace.h5",
        ]
        for ws in ws_files:
            assert not ws.is_file()

        args = {
            "debug": False,
            "quiet": False,
            "event_id": EVENT_IDS,
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

        subcommand = "assemble"
        step_args = {
            "subcommand": subcommand,
            "func": app.classes[subcommand]["class"],
            "log": None,
        }
        args.update(step_args)
        app.main(**args)

        for ws in ws_files:
            assert ws.is_file()

        ws_files[1].unlink()

        args = {
            "debug": False,
            "quiet": False,
            "event_id": EVENT_IDS,
            "textfile": None,
            "overwrite": False,
            "num_processes": 0,
            "label": None,
            "datadir": ddir,
            "confdir": cdir,
            "resume": "usp000hzq8",
        }
        subcommand = "assemble"
        step_args = {
            "subcommand": subcommand,
            "func": app.classes[subcommand]["class"],
            "log": None,
        }
        args.update(step_args)
        app.main(**args)

        for ws in ws_files:
            assert ws.is_file()

    except Exception as ex:
        raise ex
    finally:
        # Remove workspace and image files
        pattern = ["workspace.h5", ".png"]
        for root, _, files in os.walk(ddir):
            for file in files:
                if any(file.endswith(ext) for ext in pattern):
                    os.remove(os.path.join(root, file))


def test_assemble():
    EVENT_ID = "ci38457511"
    WORKSPACE_ITEMS = (
        "AuxiliaryData",
        "AuxiliaryData/StreamProcessingParameters",
        "AuxiliaryData/StreamProcessingParameters/CI.CCC",
        "AuxiliaryData/StreamProcessingParameters/CI.CCC/CI.CCC.--.HN_ci38457511_unprocessed",
        "AuxiliaryData/StreamProcessingParameters/CI.CLC",
        "AuxiliaryData/StreamProcessingParameters/CI.CLC/CI.CLC.--.HN_ci38457511_unprocessed",
        "AuxiliaryData/StreamProcessingParameters/CI.TOW2",
        "AuxiliaryData/StreamProcessingParameters/CI.TOW2/CI.TOW2.--.HN_ci38457511_unprocessed",
        "AuxiliaryData/StreamSupplementalStats",
        "AuxiliaryData/StreamSupplementalStats/CI.CCC",
        "AuxiliaryData/StreamSupplementalStats/CI.CCC/CI.CCC.--.HN_ci38457511_unprocessed",
        "AuxiliaryData/StreamSupplementalStats/CI.CLC",
        "AuxiliaryData/StreamSupplementalStats/CI.CLC/CI.CLC.--.HN_ci38457511_unprocessed",
        "AuxiliaryData/StreamSupplementalStats/CI.TOW2",
        "AuxiliaryData/StreamSupplementalStats/CI.TOW2/CI.TOW2.--.HN_ci38457511_unprocessed",
        "AuxiliaryData/TraceProcessingParameters",
        "AuxiliaryData/TraceProcessingParameters/CI.CCC",
        "AuxiliaryData/TraceProcessingParameters/CI.CCC/CI.CCC.--.HN1_ci38457511_unprocessed",
        "AuxiliaryData/TraceProcessingParameters/CI.CCC/CI.CCC.--.HN2_ci38457511_unprocessed",
        "AuxiliaryData/TraceProcessingParameters/CI.CCC/CI.CCC.--.HNZ_ci38457511_unprocessed",
        "AuxiliaryData/TraceProcessingParameters/CI.CLC",
        "AuxiliaryData/TraceProcessingParameters/CI.CLC/CI.CLC.--.HN1_ci38457511_unprocessed",
        "AuxiliaryData/TraceProcessingParameters/CI.CLC/CI.CLC.--.HN2_ci38457511_unprocessed",
        "AuxiliaryData/TraceProcessingParameters/CI.CLC/CI.CLC.--.HNZ_ci38457511_unprocessed",
        "AuxiliaryData/TraceProcessingParameters/CI.TOW2",
        "AuxiliaryData/TraceProcessingParameters/CI.TOW2/CI.TOW2.--.HN1_ci38457511_unprocessed",
        "AuxiliaryData/TraceProcessingParameters/CI.TOW2/CI.TOW2.--.HN2_ci38457511_unprocessed",
        "AuxiliaryData/TraceProcessingParameters/CI.TOW2/CI.TOW2.--.HNZ_ci38457511_unprocessed",
        "AuxiliaryData/config",
        "AuxiliaryData/config/config",
        "AuxiliaryData/gmprocess_version",
        "AuxiliaryData/gmprocess_version/version",
        "Provenance",
        "Provenance/CI.CCC.--.HN1_ci38457511_unprocessed",
        "Provenance/CI.CCC.--.HN2_ci38457511_unprocessed",
        "Provenance/CI.CCC.--.HNZ_ci38457511_unprocessed",
        "Provenance/CI.CLC.--.HN1_ci38457511_unprocessed",
        "Provenance/CI.CLC.--.HN2_ci38457511_unprocessed",
        "Provenance/CI.CLC.--.HNZ_ci38457511_unprocessed",
        "Provenance/CI.TOW2.--.HN1_ci38457511_unprocessed",
        "Provenance/CI.TOW2.--.HN2_ci38457511_unprocessed",
        "Provenance/CI.TOW2.--.HNZ_ci38457511_unprocessed",
        "Provenance/unprocessed",
        "QuakeML",
        "Waveforms",
        "Waveforms/CI.CCC",
        "Waveforms/CI.CCC/CI.CCC.--.HN1__2019-07-06T03:19:37__2019-07-06T03:25:31__ci38457511_unprocessed",
        "Waveforms/CI.CCC/CI.CCC.--.HN2__2019-07-06T03:19:37__2019-07-06T03:25:31__ci38457511_unprocessed",
        "Waveforms/CI.CCC/CI.CCC.--.HNZ__2019-07-06T03:19:37__2019-07-06T03:25:31__ci38457511_unprocessed",
        "Waveforms/CI.CCC/StationXML",
        "Waveforms/CI.CLC",
        "Waveforms/CI.CLC/CI.CLC.--.HN1__2019-07-06T03:16:08__2019-07-06T03:21:27__ci38457511_unprocessed",
        "Waveforms/CI.CLC/CI.CLC.--.HN2__2019-07-06T03:16:08__2019-07-06T03:21:27__ci38457511_unprocessed",
        "Waveforms/CI.CLC/CI.CLC.--.HNZ__2019-07-06T03:16:08__2019-07-06T03:21:27__ci38457511_unprocessed",
        "Waveforms/CI.CLC/StationXML",
        "Waveforms/CI.TOW2",
        "Waveforms/CI.TOW2/CI.TOW2.--.HN1__2019-07-06T03:19:31__2019-07-06T03:25:26__ci38457511_unprocessed",
        "Waveforms/CI.TOW2/CI.TOW2.--.HN2__2019-07-06T03:19:31__2019-07-06T03:25:26__ci38457511_unprocessed",
        "Waveforms/CI.TOW2/CI.TOW2.--.HNZ__2019-07-06T03:19:31__2019-07-06T03:25:26__ci38457511_unprocessed",
        "Waveforms/CI.TOW2/StationXML",
    )

    try:
        cdir = constants.CONFIG_PATH_TEST
        ddir = constants.TEST_DATA_DIR / "demo"

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

        subcommand = "assemble"
        step_args = {
            "subcommand": subcommand,
            "func": app.classes[subcommand]["class"],
            "log": None,
        }
        args.update(step_args)
        app.main(**args)

        ws_filename = ddir / EVENT_ID / constants.WORKSPACE_NAME
        tests_utils.check_workspace(ws_filename, WORKSPACE_ITEMS)

    except Exception as ex:
        raise ex
    finally:
        # Remove workspace and image files
        pattern = ["workspace.h5", ".png"]
        for root, _, files in os.walk(ddir):
            for file in files:
                if any(file.endswith(ext) for ext in pattern):
                    os.remove(os.path.join(root, file))
