"""Module for pytest config options."""

import os
import shutil

from gmprocess.utils import constants

#
# This is needed here so that the matplotlib backend gets
# set before any other imports of matplotlib
#
import matplotlib

matplotlib.use("Agg")


def pytest_configure(config):
    #
    # This tells get_config_paths() (shakemap.utils.config) to
    # return paths into the testing part of the repo
    #
    os.environ["CALLED_FROM_PYTEST"] = "True"
    constants.CONFIG_PATH_TEST.mkdir()
    src = constants.DATA_DIR / "config_test.yml"
    dst = constants.CONFIG_PATH_TEST / "config_test.yml"
    shutil.copy(src, dst)


def pytest_unconfigure(config):
    del os.environ["CALLED_FROM_PYTEST"]
    shutil.rmtree(constants.CONFIG_PATH_TEST, ignore_errors=True)
