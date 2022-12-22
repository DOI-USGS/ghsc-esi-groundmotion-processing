#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import shutil
from pathlib import Path

from gmprocess.utils import constants
from gmprocess.utils.test_utils import vcr


@vcr.use_cassette()
def test_download(script_runner):
    try:
        # Need to create profile first.
        cdir = constants.CONFIG_PATH_TEST
        ddir = str(cdir / "data")
        setup_inputs = io.StringIO(f"test\n{cdir}\n{ddir}\nname\ntest@email.com\n")
        ret = script_runner.run("gmrecords", "projects", "-c", stdin=setup_inputs)
        setup_inputs.close()
        assert ret.success

        ret = script_runner.run("gmrecords", "-e", "us10008dkr", "download")
        assert ret.success

    except Exception as ex:
        raise ex
    finally:
        shutil.rmtree(constants.CONFIG_PATH_TEST)


@vcr.use_cassette()
def test_download_single_provider(script_runner):
    # This test is to specify a single provider and it's URL
    try:
        # Need to create profile first.
        cdir = constants.CONFIG_PATH_TEST
        ddir = str(cdir / "data")
        setup_inputs = io.StringIO(f"test\n{cdir}\n{ddir}\nname\ntest@email.com\n")
        ret = script_runner.run("gmrecords", "projects", "-c", stdin=setup_inputs)
        setup_inputs.close()
        assert ret.success

        # Copy over relevant config
        test_conf_file = constants.TEST_DATA_DIR / "config_download_single_provider.yml"
        shutil.copy(test_conf_file, constants.CONFIG_PATH_TEST / "user.yml")

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


@vcr.use_cassette()
def test_download_provider_url(script_runner):
    # This test is to specify a single provider and it's URL
    try:
        # Need to create profile first.
        cdir = constants.CONFIG_PATH_TEST
        ddir = str(cdir / "data")
        setup_inputs = io.StringIO(f"test\n{cdir}\n{ddir}\nname\ntest@email.com\n")
        ret = script_runner.run("gmrecords", "projects", "-c", stdin=setup_inputs)
        setup_inputs.close()
        assert ret.success

        # Copy over relevant config
        test_conf_file = constants.TEST_DATA_DIR / "config_download_provider_url.yml"
        shutil.copy(test_conf_file, constants.CONFIG_PATH_TEST / "user.yml")
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


if __name__ == "__main__":
    test_download()
    test_download_single_provider()
    test_download_provider_url()
