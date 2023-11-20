from gmprocess.io import report


def test_report(load_ci38457511_demo_export, tmp_path):
    ws = load_ci38457511_demo_export
    sc = ws.get_streams("ci38457511")
    event = ws.get_event("ci38457511")

    report.build_report_latex(
        st_list=sc.streams,
        directory=tmp_path,
        event=event,
        prefix="pytest",
        build_latex=False,
    )
