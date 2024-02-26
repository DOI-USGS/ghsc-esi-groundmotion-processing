import shutil

from ruamel.yaml import YAML

from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.utils.constants import TEST_DATA_DIR


def test_gmprocess_config_test(tmp_path, script_runner):
    test_dir = TEST_DATA_DIR / "demo_steps" / "process_waveforms" / "ci38457511"
    src_ws_file = test_dir / "workspace.h5"
    dst_ws_file = tmp_path / "workspace.h5"
    dst_config_file = tmp_path / "test.yml"
    if dst_config_file.exists():
        dst_config_file.unlink()

    shutil.copy(str(src_ws_file), str(dst_ws_file))
    ws = StreamWorkspace(dst_ws_file)

    # Save the config to a file
    ret = script_runner.run(
        "gmprocess_config", "--workspace", dst_ws_file, "--save", dst_config_file
    )
    assert ret.success
    assert dst_config_file.exists()
    assert not ws.config["fetchers"]["search_parameters"]["enabled"]
    ws.close()

    # Read in config file
    yaml = YAML()
    with open(dst_config_file, "r", encoding="utf-8") as f:
        yaml.preserve_quotes = True
        test_config = yaml.load(f)

    # Change a value
    test_config["fetchers"]["search_parameters"]["enabled"] = True
    dst_config_file.unlink()
    yaml.indent(mapping=4)
    yaml.preserve_quotes = True
    with open(dst_config_file, "a", encoding="utf-8") as yf:
        yaml.dump(test_config, yf)

    # Update the workspace file
    ret = script_runner.run(
        "gmprocess_config", "--workspace", dst_ws_file, "--update", dst_config_file
    )
    assert ret.success

    # Read workspace file
    ws = StreamWorkspace(dst_ws_file)

    # Check that update from file was made
    assert ws.config["fetchers"]["search_parameters"]["enabled"] is True
