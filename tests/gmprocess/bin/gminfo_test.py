import shutil
from pathlib import Path

from gmprocess.utils.constants import TEST_DATA_DIR
from gmprocess.bin.gminfo import App

def test_gminfo():
    input_dir = TEST_DATA_DIR / "geonet" / "nz2018p115908"
    out_dir = Path("temp_dir")
    out_dir.mkdir(exist_ok=True)

    try:
        # Concise output, save to file
        app = App()
        app.main(str(input_dir), True, str(out_dir / 'test.csv'), False)
        assert (out_dir / "test.csv").exists()
        assert (out_dir / "test_errors.csv").exists()

        app = App()
        app.main(str(input_dir))

    except Exception as e:
        raise e
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)
