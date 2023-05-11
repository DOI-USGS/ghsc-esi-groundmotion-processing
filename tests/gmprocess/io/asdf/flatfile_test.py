#!/usr/bin/env python

import os

import numpy as np

from gmprocess.utils import constants
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.io.asdf.flatfile import Flatfile


def test_flatfile():
    ddir = constants.TEST_DATA_DIR / "demo_steps" / "exports" / "ci38457511"
    ws_file = ddir / "workspace.h5"
    ws = StreamWorkspace(ws_file)
    ff = Flatfile(ws)
    spect_table, _ = ff.get_fit_spectra_table()
    target_f0 = np.array(
        [
            0.18404403,
            0.14632835,
            0.47972901,
            0.02019254,
            0.03875098,
            0.05347112,
            0.13864016,
            0.09723006,
            0.19382767,
        ]
    )
    np.testing.assert_allclose(spect_table["f0"], target_f0)

    snr_table, _ = ff.get_snr_table()
    target_snr = np.array(
        [
            1.36913029e04,
            1.36827316e04,
            9.31650424e03,
            4.96294139e01,
            1.19447091e01,
            2.39717323e01,
            5.84182387e03,
            3.99108685e03,
            1.89513166e03,
        ]
    )
    np.testing.assert_allclose(snr_table["SNR(1)"], target_snr)

    event_table, imc_tables, _ = ff.get_tables()
    np.testing.assert_allclose(event_table["magnitude"][0], 7.1)
    assert len(imc_tables) == 4
    rot50_table = imc_tables["ROTD50.0"]
    target_sa = np.array([53.144627, 17.922639, 41.612646])
    np.testing.assert_allclose(rot50_table["SA(1.000)"], target_sa)


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_flatfile()
