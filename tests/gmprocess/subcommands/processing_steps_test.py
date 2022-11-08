#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
import shutil

from gmprocess.utils import constants


def test_processing_steps(script_runner):
    try:
        # Need to create profile first.
        cdir = str(constants.CONFIG_PATH_TEST)
        ddir = str(constants.TEST_DATA_DIR / "demo")
        setup_inputs = io.StringIO(f"test\n{cdir}\n{ddir}\nname\ntest@email.com\n")
        ret = script_runner.run("gmrecords", "projects", "-c", stdin=setup_inputs)
        setup_inputs.close()
        assert ret.success

        ret = script_runner.run(
            "gmrecords",
            "processing_steps",
        )
        assert ret.success

    except Exception as ex:
        raise ex
    finally:
        shutil.rmtree(constants.CONFIG_PATH_TEST)


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_processing_steps()
