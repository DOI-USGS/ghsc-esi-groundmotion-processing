#!/usr/bin/env python3
"""Utility script for bundling workspace files for archiving a data release as a special project at CESMD."""


import pathlib
import shutil
import os
import io

import h5py
import obspy

GMPROCESS_ASDF_URL = (
    "https://gmprocess.readthedocs.io/en/latest/contents/manual/workspace.html"
)


class HtmlIndex:

    def __init__(self, project_name):
        self.project_name = project_name
        self.fout = None

    def open(self, filename):
        self.fout = open(filename, "w")

        lines = (
            """<!DOCTYPE html>""",
            """<html lang="en">""",
            """<body>""",
        )
        for line in lines:
            self.fout.write(line + "\n")

    def close(self):
        lines = (
            """</body>""",
            """</html>""",
        )
        for line in lines:
            self.fout.write(line + "\n")

    def write_header(self):
        lines = (
            """<head>""",
            f"""<title>{self.project_name}_timeseries</title>""",
            """<meta charset="utf-8">""",
            """<meta name="viewport" content="width=device-width, initial-scale=1">""",
            """</head>""",
            """<style>""",
            """table, th, td { border: 1px solid grey; text-align: center; }""",
            """</style>""",
        )
        for line in lines:
            self.fout.write(line + "\n")

    def write_summary(self, title: str):
        lines = (
            """<p style="padding-top:10px"><a href = "https://strongmotioncenter.org/specialstudies/{self.project_name}/">[Project page]</a></p>""",
            f"""<h2>{title}</h2>""",
            "",
            """<h3>Timeseries Data</h3>""",
            """<p><a href = "timeseries.zip">Download All</a></p>""",
            """<p>Documentation of the ASDF files containing the time series data can be found in the <a href="{GMPROCESS_ASDF_URL}" target="_blank">gmprocess documentation</a>.</p>""",
        )
        for line in lines:
            self.fout.write(line + "\n")

    def write_table(self, event_info: list):
        lines = (
            """<p>Earthquake are ordered by origin time.</p>""",
            """<table style = "width: 30%">""",
            """\t<tr>""",
            """\t\t<th style = "width: 20%">Filename</th>""",
            """\t\t<th style = "width: 12.5%">Event ID</th>""",
            """\t\t<th style = "width: 12.5%">Filesize</th>""",
            """\t</tr>""",
        )
        for eq_id, file_size in event_info:
            lines += (
                """\t<tr>""",
                f"""\t\t<td><a href="datafiles/{eq_id}.h5">{eq_id}.h5</a></td>""",
                f"""\t\t<td><a href="https://earthquake.usgs.gov/earthquakes/eventpage/{eq_id}/executive" target="_blank"">{eq_id}</a></td>""",
                f"""\t\t<td>{file_size}</td>""",
                """\t</tr>""",
            )
        for line in lines:
            self.fout.write(line + "\n")


class DataReleaseApp:

    def main(self, project_name: str, project_title: str, data_dir: pathlib.Path):
        self.project_name = project_name
        self.project_title = project_title
        self.data_dir = data_dir
        self.out_dir = pathlib.Path(project_name)
        self.out_dir.mkdir(exist_ok=True)

        event_ids = self._get_event_ids()
        self.export_workspaces(event_ids)
        self.generate_index(event_ids)

    def export_workspaces(self, event_ids):
        dest_dir = self.out_dir / "timeseries" / "datafiles"
        dest_dir.mkdir(parents=True, exist_ok=True)
        for event_id in event_ids:
            filename_src = self.data_dir / event_id / "workspace.h5"
            filename_dest = dest_dir / f"{event_id}.h5"
            shutil.copy(filename_src, filename_dest)

    def generate_index(self, event_ids):
        filename = self.out_dir / "timeseries" / "index.html"
        html = HtmlIndex(self.project_name)
        html.open(filename)
        html.write_header()
        html.write_summary(self.project_title)
        event_info = [(event_id, self._file_size(event_id)) for event_id in event_ids]
        html.write_table(event_info)
        html.close()

    def _get_event_ids(self):
        """Get event ids sorted by origin time."""
        workspace_files = self.data_dir.glob("*/workspace.h5")
        events = []
        for workspace in workspace_files:
            event = self._get_event(workspace)
            event_id = event.resource_id.id.split("/")[-1]
            origin_time = event.origins[0].time
            events.append((event_id, origin_time))
        events = sorted(events, key=lambda event: event[1])
        return [event[0] for event in events]

    def _get_event(self, filename):
        h5 = h5py.File(filename)
        bytes = io.BytesIO(h5["QuakeML"][:])
        return obspy.read_events(bytes)[0]

    def _file_size(self, event_id):
        filename = self.data_dir / event_id / "workspace.h5"
        nbytes = os.path.getsize(filename)
        if nbytes >= 2**30:
            size = f"{nbytes / 2**30:.2f} GB"
        elif nbytes >= 2**20:
            size = f"{nbytes / 2**20:.2f} MB"
        else:
            size = f"{nbytes // 2**10:.2f} KB"
        return size


def cli():
    """Command line interface"""
    DESCRIPTION = "Application for bundling workspace files for archiving a data release as a special project at CESMD."

    import argparse

    parser = argparse.ArgumentParser(
        description=DESCRIPTION, formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--project",
        action="store",
        dest="project",
        required=True,
        help="CESMD project identifier",
    )
    parser.add_argument(
        "--title", action="store", dest="title", required=True, help="Title of project"
    )
    parser.add_argument(
        "--data-dir",
        action="store",
        dest="data_dir",
        required=True,
        help="Data directory containing events.",
    )
    args = parser.parse_args()

    app = DataReleaseApp()
    kwds = {
        "project_name": args.project,
        "project_title": args.title,
        "data_dir": pathlib.Path(args.data_dir).expanduser(),
    }
    app.main(**kwds)


if __name__ == "__main__":
    cli()
