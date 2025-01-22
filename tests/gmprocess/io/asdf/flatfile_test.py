import numpy as np

from gmprocess.io.asdf.flatfile import Flatfile


def test_flatfile_nc73821036(load_nc73821036_psa_psv):
    ws = load_nc73821036_psa_psv
    ff = Flatfile(ws)
    _, imc_tables, _ = ff.get_tables()
    assert len(imc_tables) == 6
    rot50_table = imc_tables["RotD(percentile=50.0)"]
    target_psa = np.array([24.236534])
    np.testing.assert_allclose(
        rot50_table["PSA(T=1.0000, D=0.050)"], target_psa, atol=1e-6
    )


def test_flatfile_ci38457511(load_ci38457511_demo_export):
    ws = load_ci38457511_demo_export
    ff = Flatfile(ws)
    spect_table, _ = ff.get_fit_spectra_table()
    target_f0 = np.array(
        [
            0.18030727,
            0.12870161,
            0.42279639,
            0.09750444,
            0.03381905,
            0.09792278,
            0.06558186,
            0.08157319,
            0.19361113,
        ]
    )
    np.testing.assert_allclose(spect_table["f0"], target_f0, atol=1e-7)

    snr_table, _ = ff.get_snr_table()
    target_snr = np.array(
        [
            4699.60779086,
            4666.11659722,
            3189.73061953,
            54.09734581,
            13.31423377,
            27.1675575,
            2016.06165194,
            1414.12885504,
            676.57124717,
        ]
    )
    np.testing.assert_allclose(snr_table["SNR(1)"], target_snr, atol=1e-7)

    event_table, imc_tables, _ = ff.get_tables()
    np.testing.assert_allclose(event_table["magnitude"][0], 7.1)
    assert len(imc_tables) == 6
    rot50_table = imc_tables["RotD(percentile=50.0)"]
    target_sa = np.array([53.08626, 17.908144, 41.625575])
    np.testing.assert_allclose(
        rot50_table["SA(T=1.0000, D=0.050)"], target_sa, atol=1e-6
    )
