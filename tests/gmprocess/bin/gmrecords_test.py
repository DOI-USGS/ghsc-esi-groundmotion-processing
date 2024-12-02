import io
import shutil

from gmprocess.utils import constants


def test_gmrecords(script_runner):
    try:
        # Need to create profile first.
        setup_inputs = io.StringIO("test\n\n\nname\ntest@email.com\n")
        ret = script_runner.run("gmrecords", "projects", "-c", stdin=setup_inputs)
        setup_inputs.close()
        assert ret.success

        ret = script_runner.run("gmrecords", "--version")
        assert ret.success

        ret = script_runner.run("gmrecords", "--help")
        assert ret.success
    except Exception as ex:
        raise ex
