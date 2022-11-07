#!/usr/bin/env python
# -*- coding: utf-8 -*-

# stdlib imports
import os.path
import tempfile
import shutil
from pathlib import Path

# third party imports
import pandas as pd

from gmprocess.io.read import read_data
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.utils import constants
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.utils.plot import plot_oscillators
from gmprocess.utils.plot import plot_moveout
from gmprocess.utils.plot import plot_regression
from gmprocess.utils.plot import summary_plots


def test_summary_plots():
    ddir = constants.TEST_DATA_DIR / "demo_steps" / "exports" / "ci38457511"
    ws = StreamWorkspace.open(ddir / "workspace.h5")
    event = ws.getEvent("ci38457511")
    st = ws.getStreams(eventid="ci38457511")[0]
    tdir = tempfile.mkdtemp()
    try:
        summary_plots(st, tdir, event)
    except Exception as e:
        raise e
    finally:
        shutil.rmtree(tdir, ignore_errors=True)


def test_regression():
    event_file = constants.TEST_DATA_DIR / "events.xlsx"
    imc_file = constants.TEST_DATA_DIR / "greater_of_two_horizontals.xlsx"
    imc = "G2H"
    event_table = pd.read_excel(str(event_file), engine="openpyxl")
    imc_table = pd.read_excel(str(imc_file), engine="openpyxl")
    imt = "PGA"

    tdir = tempfile.mkdtemp()
    try:
        tfile = os.path.join(tdir, "regression.png")
        tfile = os.path.join(os.path.expanduser("~"), "regression.png")
        plot_regression(event_table, imc, imc_table, imt, tfile, colormap="jet")
        print(tfile)
    except Exception as e:
        raise e
    finally:
        shutil.rmtree(tdir, ignore_errors=True)


def test_plot():
    # read in data
    datafiles, _ = read_data_dir("cwb", "us1000chhc", "2-ECU.dat")
    st = read_data(datafiles[0])[0]

    # Moveout plots
    epicenter_lat = 24.14
    epicenter_lon = 121.69
    plot_moveout(
        [st],
        epicenter_lat,
        epicenter_lon,
        "1",
        figsize=(15, 10),
        minfontsize=16,
        normalize=True,
        factor=0.1,
    )


def test_plot_oscillators():
    ddir = constants.TEST_DATA_DIR / "demo_steps" / "exports" / "ci38457511"
    ws = StreamWorkspace.open(ddir / "workspace.h5")
    st = ws.getStreams(eventid="ci38457511")[0]
    tdir = Path(tempfile.mkdtemp())
    filepath = tdir / "oscillator_plot.png"
    try:
        plot_oscillators(st, file=filepath)
    except Exception as e:
        raise e
    finally:
        shutil.rmtree(tdir, ignore_errors=True)


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_regression()
    test_plot()
    test_summary_plots()
    test_plot_oscillators()
