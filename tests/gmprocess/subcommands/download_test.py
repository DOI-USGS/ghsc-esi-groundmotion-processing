import io
import os
import shutil
from pathlib import Path

from gmprocess.apps.gmrecords import GMrecordsApp
from gmprocess.utils import constants
from gmprocess.utils.tests_utils import vcr

DATA_DIR = constants.DATA_DIR


@vcr.use_cassette()
def _test_download():
    try:
        event_id = "nc72282711"
        cdir = constants.CONFIG_PATH_TEST
        cdir.mkdir(exist_ok=True)
        ddir = cdir / "data"
        ddir.mkdir(exist_ok=True)
        src_conf = DATA_DIR / constants.CONFIG_FILE_TEST_DOWNLOAD
        dst_conf = cdir / constants.CONFIG_FILE_TEST_DOWNLOAD
        shutil.copy(src_conf, dst_conf)
        app = GMrecordsApp()
        app.load_subcommands()
        step = "download"
        args = {
            "event_id": event_id,
            "datadir": str(ddir),
            "confdir": str(cdir),
            "debug": False,
            "quiet": False,
            "textfile": None,
            "overwrite": False,
            "num_processes": 0,
            "label": None,
            "resume": None,
        }
        step_args = {
            "subcommand": step,
            "func": app.classes[step]["class"],
            "log": None,
        }
        args.update(step_args)
        app.main(**args)

        rdir = ddir / event_id / "raw"
        dfiles = list(rdir.glob("*"))
        assert len(dfiles) == 8

    except Exception as ex:
        raise ex
    finally:
        shutil.rmtree(constants.CONFIG_PATH_TEST)


@vcr.use_cassette()
def _test_download_single_provider(script_runner):
    # This test is to specify a single provider and it's URL
    try:
        # Need to create profile first.
        cdir = constants.CONFIG_PATH_TEST
        ddir = str(cdir / "data")
        setup_inputs = io.StringIO(f"test\n{cdir}\n{ddir}\nname\ntest@email.com\n")
        ret = script_runner.run("gmrecords", "projects", "-c", stdin=setup_inputs)
        setup_inputs.close()
        assert ret.success

        # Set env variable to let gmrecords know we need a specific config here
        os.environ["TEST_SPECIFIC_CONF"] = "True"
        test_conf_file = constants.TEST_DATA_DIR / "config_download_single_provider.yml"
        os.environ["TEST_SPECIFIC_CONF_FILE"] = str(test_conf_file)

        ret = script_runner.run("gmrecords", "-e", "nc73821036", "download")
        assert ret.success

        raw_dir = Path(ddir) / "nc73821036" / "raw"
        assert raw_dir.exists()

        tfile = list(
            raw_dir.glob("UW.BROK..HNN__20221220T103414Z__20221220T103624Z.mseed")
        )
        assert len(tfile) == 1

    except Exception as ex:
        raise ex
    finally:
        shutil.rmtree(constants.CONFIG_PATH_TEST)
        del os.environ["TEST_SPECIFIC_CONF"]
        del os.environ["TEST_SPECIFIC_CONF_FILE"]


@vcr.use_cassette()
def _test_download_provider_url(script_runner):
    # This test is to specify a single provider and it's URL
    try:
        # Need to create profile first.
        cdir = constants.CONFIG_PATH_TEST
        ddir = str(cdir / "data")
        setup_inputs = io.StringIO(f"test\n{cdir}\n{ddir}\nname\ntest@email.com\n")
        ret = script_runner.run("gmrecords", "projects", "-c", stdin=setup_inputs)
        setup_inputs.close()
        assert ret.success

        # Set env variable to let gmrecords know we need a specific config here
        os.environ["TEST_SPECIFIC_CONF"] = "True"
        test_conf_file = constants.TEST_DATA_DIR / "config_download_provider_url.yml"
        os.environ["TEST_SPECIFIC_CONF_FILE"] = str(test_conf_file)

        event_file = constants.TEST_DATA_DIR / "israel_event_test.csv"

        ret = script_runner.run("gmrecords", "-t", str(event_file), "download")
        assert ret.success

        raw_dir = Path(ddir) / "gsi200801041549" / "raw"
        assert raw_dir.exists()
        tfile = list(
            raw_dir.glob("IS.MMA3..BHZ__20080401T174930Z__20080401T175700Z.mseed")
        )
        assert len(tfile) == 1

    except Exception as ex:
        raise ex
    finally:
        shutil.rmtree(constants.CONFIG_PATH_TEST)
        del os.environ["TEST_SPECIFIC_CONF"]
        del os.environ["TEST_SPECIFIC_CONF_FILE"]


@vcr.use_cassette()
def _test_download_provider_url_bounds(script_runner):
    # This test is to specify a single provider and it's URL
    try:
        # Need to create profile first.
        cdir = constants.CONFIG_PATH_TEST
        ddir = str(cdir / "data")
        setup_inputs = io.StringIO(f"test\n{cdir}\n{ddir}\nname\ntest@email.com\n")
        ret = script_runner.run("gmrecords", "projects", "-c", stdin=setup_inputs)
        setup_inputs.close()
        assert ret.success

        # Set env variable to let gmrecords know we need a specific config here
        os.environ["TEST_SPECIFIC_CONF"] = "True"
        test_conf_file = (
            constants.TEST_DATA_DIR / "config_download_provider_url_bounds.yml"
        )
        os.environ["TEST_SPECIFIC_CONF_FILE"] = str(test_conf_file)

        event_file = constants.TEST_DATA_DIR / "israel_event_test.csv"

        ret = script_runner.run("gmrecords", "-t", str(event_file), "download")
        assert ret.success

        raw_dir = Path(ddir) / "gsi200801041549" / "raw"
        assert raw_dir.exists()

        tfile = list(
            raw_dir.glob("IS.MMA3..BHZ__20080401T174930Z__20080401T175700Z.mseed")
        )
        assert len(tfile) == 1

        ret = script_runner.run("gmrecords", "-e hv73325052", "download")
        assert ret.success

        raw_dir = Path(ddir) / "hv73325052" / "raw"
        assert raw_dir.exists()

        tfile = list(raw_dir.glob("*.mseed"))
        assert len(tfile) == 0

    except Exception as ex:
        raise ex
    finally:
        shutil.rmtree(constants.CONFIG_PATH_TEST)
        del os.environ["TEST_SPECIFIC_CONF"]
        del os.environ["TEST_SPECIFIC_CONF_FILE"]
