from gmprocess.io.asdf.core import is_asdf, read_asdf, write_asdf
from gmprocess.utils import constants


def test_asdf(load_data_us1000778i, configure_strec, tmp_path):
    raw_streams, event = load_data_us1000778i
    existing_config_data = configure_strec
    try:
        tfile = tmp_path / "test.hdf"
        try:
            write_asdf(tfile, raw_streams, event, label="default")
            assert is_asdf(tfile)
            outstreams = read_asdf(tfile)
            assert len(outstreams) == len(raw_streams)

            write_asdf(tfile, raw_streams, event, label="foo")
            outstreams2 = read_asdf(tfile, label="foo")
            assert len(outstreams2) == len(raw_streams)
        finally:
            if existing_config_data is not None:
                with open(constants.STREC_CONFIG_PATH, "wt", encoding="utf-8") as f:
                    f.write(existing_config_data)

    except Exception as e:
        raise (e)
