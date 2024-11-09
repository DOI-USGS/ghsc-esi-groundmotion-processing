import pathlib
import shutil
import tempfile

from esi_utils_io.cmd import get_command_output
from gmprocess.utils.tests_utils import vcr

PROJ_STR = """project = pytest
[projects]
[[pytest]]
conf_path = [confdir]
data_path = [datadir]
"""
PROJ_PATH = pathlib.Path(".") / ".gmprocess"


@vcr.use_cassette()
def test_fetch_orfeus():
    eqid = "us10005c3r"
    tmp_dir = pathlib.Path(tempfile.mkdtemp())
    try:
        conf_dir = tmp_dir / "conf"
        data_dir = tmp_dir / "data"
        conf_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)
        PROJ_PATH.mkdir(parents=True, exist_ok=True)
        proj_conf = PROJ_PATH / "projects.conf"
        proj_str = PROJ_STR.replace("[confdir]", str(conf_dir))
        proj_str = proj_str.replace("[datadir]", str(data_dir))
        with proj_conf.open("w", encoding="utf-8") as f:
            f.write(proj_str)
        with open(proj_conf, "r", encoding="utf-8") as f:
            print(f.read())
        cmd = (
            f"fetch_orfeus --event-ids={eqid} "
            "--fetch-waveforms "
            "--processing-type MP "
            "--to-gmprocess"
        )
        rc, so, se = get_command_output(cmd)
        assert rc
    finally:
        shutil.rmtree(PROJ_PATH, ignore_errors=True)
        shutil.rmtree(tmp_dir, ignore_errors=True)
        shutil.rmtree("data-waveforms", ignore_errors=True)
