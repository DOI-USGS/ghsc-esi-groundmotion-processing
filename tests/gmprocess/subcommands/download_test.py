#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import shutil

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


if __name__ == "__main__":
    test_download()
