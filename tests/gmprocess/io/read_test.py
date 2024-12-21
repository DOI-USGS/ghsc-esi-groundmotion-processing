import copy

from gmprocess.io.read import read_data, _get_format, _validate_format
from gmprocess.utils.tests_utils import read_data_dir


def test_read(config):
    conf = copy.deepcopy(config)

    cosmos_files, _ = read_data_dir("cosmos", "ci14155260", "Cosmos12TimeSeriesTest.v1")
    cwa_files, _ = read_data_dir("cwa", "us1000chhc", "1-EAS.dat")
    dmg_files, _ = read_data_dir("dmg", "nc71734741", "CE89146.V2")
    geonet_files, _ = read_data_dir(
        "geonet", "us1000778i", "20161113_110300_HSES_20.V1A"
    )
    knet_files, _ = read_data_dir("knet", "us2000cnnl", "AOM0011801241951.EW")
    smc_files, _ = read_data_dir("smc", "nc216859", "0111a.smc")

    file_dict = {}
    file_dict["cosmos"] = cosmos_files[0]
    file_dict["cwb"] = cwa_files[0]
    file_dict["dmg"] = dmg_files[0]
    file_dict["geonet"] = geonet_files[0]
    file_dict["knet"] = knet_files[0]
    file_dict["smc"] = smc_files[0]

    for file_format, file_name in file_dict.items():
        assert _get_format(file_name, conf) == file_format
        assert _validate_format(file_name, conf, file_format) == file_format

    assert _validate_format(file_dict["knet"], conf, "smc") == "knet"
    assert _validate_format(file_dict["dmg"], conf, "cosmos") == "dmg"
    assert _validate_format(file_dict["cosmos"], conf, "invalid") == "cosmos"

    for file_format, file_name in file_dict.items():
        try:
            stream = read_data(file_name, conf, file_format)[0]
        except Exception:
            pass
        assert stream[0].stats.standard["source_format"] == file_format
        stream = read_data(file_name)[0]
        assert stream[0].stats.standard["source_format"] == file_format
    # test exception
    try:
        file_path = smc_files[0].replace("0111a.smc", "not_a_file.smc")
        read_data(file_path)[0]
        success = True
    except BaseException:
        success = False
    assert not success
