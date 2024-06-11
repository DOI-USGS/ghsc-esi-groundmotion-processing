import numpy as np

from gmprocess.io.asdf.flatfile import Flatfile


def test_flatfile(load_ci38457511_demo_export):
    ws = load_ci38457511_demo_export
    ff = Flatfile(ws)
    spect_table, _ = ff.get_fit_spectra_table()
    target_f0 = np.array(
        [
            0.184331412949,
            0.146276292955,
            0.480365487228,
            0.020329709006,
            0.038951622906,
            0.004691576598,
            0.139481632418,
            0.097327682036,
            0.194052895563,
        ]
    )
    np.testing.assert_allclose(spect_table["f0"], target_f0)

    snr_table, _ = ff.get_snr_table()
    target_snr = np.array(
        [
            4.6524055383e03,
            4.6494923423e03,
            3.1654944033e03,
            5.5508988924e01,
            1.3659890143e01,
            2.7015974078e01,
            2.1172353792e03,
            1.4461666852e03,
            6.8618301565e02,
        ]
    )
    np.testing.assert_allclose(snr_table["SNR(1)"], target_snr)

    event_table, imc_tables, _ = ff.get_tables()
    np.testing.assert_allclose(event_table["magnitude"][0], 7.1)
    assert len(imc_tables) == 6
    rot50_table = imc_tables["RotD(percentile=50.0)"]
    target_sa = np.array([53.133845, 17.926331, 41.583194])
    np.testing.assert_allclose(rot50_table["SA(T=1.0000, D=0.050)"], target_sa)
