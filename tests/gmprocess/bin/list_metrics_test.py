def test_list_metrics(script_runner):
    ret = script_runner.run("list_metrics")
    assert ret.success
