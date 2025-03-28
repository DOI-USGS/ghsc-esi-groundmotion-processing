import numpy as np

from gmprocess.utils.tests_utils import read_data_dir
from gmprocess.io.read import read_data


def test_uneven_samples():
    file1, _ = read_data_dir("dmg", "ci3031425", files=["NEWPORT.RAW"])
    test1 = read_data(file1[0])
    prov_resample = test1[0][0].get_provenance("resample")
    np.testing.assert_allclose(
        prov_resample[0]["prov_attributes"]["nominal_sps"], 201.32337744591487
    )
