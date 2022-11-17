#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import pathlib

from gmprocess.subcommands.lazy_loader import LazyLoader
from gmprocess.metrics.station_summary import get_ps2ff_interpolation

np = LazyLoader("np", globals(), "numpy")
ob = LazyLoader("ob", globals(), "obspy.geodetics.base")
oqgeo = LazyLoader("oqgeo", globals(), "openquake.hazardlib.geo.geodetic")
rupt = LazyLoader("rupt", globals(), "esi_utils_rupture")

arg_dicts = LazyLoader("arg_dicts", globals(), "gmprocess.subcommands.arg_dicts")
base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
utils = LazyLoader("utils", globals(), "gmprocess.utils")
rupt_utils = LazyLoader("rupt_utils", globals(), "gmprocess.utils.rupture_utils")
ws = LazyLoader("ws", globals(), "gmprocess.io.asdf.stream_workspace")
station_summary = LazyLoader(
    "station_summary", globals(), "gmprocess.metrics.station_summary"
)
confmod = LazyLoader("confmod", globals(), "gmprocess.utils.config")

M_PER_KM = 1000


class ComputeStationMetricsModule(base.SubcommandModule):
    """Compute station metrics."""

    command_name = "compute_station_metrics"
    aliases = ("sm",)

    arguments = []

    def main(self, gmrecords):
        """Compute station metrics.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info(f"Running subcommand '{self.command_name}'")

        self.gmrecords = gmrecords
        self._check_arguments()
        self._get_events()

        for ievent, event in enumerate(self.events):
            logging.info(
                f"Computing station metrics for event "
                f"{event.id} ({1+ievent} of {len(self.events)})..."
            )
            self._event_station_metrics(event)

        self._summarize_files_created()

    def _event_station_metrics(self, event):
        self.eventid = event.id
        event_dir = self.gmrecords.data_path / self.eventid
        workname = event_dir / utils.constants.WORKSPACE_NAME
        if not workname.is_file():
            logging.info(
                f"No workspace file found for event {self.eventid}. Please run "
                "subcommand 'assemble' to generate workspace file."
            )
            logging.info("Continuing to next event.")
            return event.id

        self.workspace = ws.StreamWorkspace.open(workname)
        ds = self.workspace.dataset
        self._get_labels()
        config = self._get_config()

        station_list = ds.waveforms.list()
        if not len(station_list):
            self.workspace.close()
            return event.id

        rupture_file = rupt_utils.get_rupture_file(event_dir)
        origin = rupt.origin.Origin(
            {
                "id": self.eventid,
                "netid": "",
                "network": "",
                "lat": event.latitude,
                "lon": event.longitude,
                "depth": event.depth_km,
                "locstring": "",
                "mag": event.magnitude,
                "time": event.time,
            }
        )
        self.origin = origin
        if isinstance(rupture_file, pathlib.Path):
            rupture_file = str(rupture_file)
        rupture = rupt.factory.get_rupture(origin, rupture_file)
        if isinstance(rupture, rupt.point_rupture.PointRupture):
            self._get_ps2ff(event)
        else:
            self.rrup_interp = None
            self.rjb_interp = None

        for station_id in station_list:
            streams = self.workspace.getStreams(
                event.id,
                stations=[station_id],
                labels=[self.gmrecords.args.label],
                config=config,
            )
            if not len(streams):
                logging.error(
                    "No matching streams found. Aborting computing station "
                    f"metrics for {station_id} for {event.id}."
                )
                continue

            for st in streams:
                summary = station_summary.StationSummary.from_config(
                    st,
                    event=event,
                    config=config,
                    calc_waveform_metrics=False,
                    calc_station_metrics=True,
                    rupture=rupture,
                    rrup_interp=self.rrup_interp,
                    rjb_interp=self.rjb_interp,
                )

                xmlstr = summary.get_station_xml()
                if config["read"]["use_streamcollection"]:
                    chancode = st.get_inst()
                else:
                    chancode = st[0].stats.channel
                metricpath = "/".join(
                    [
                        ws.format_netsta(st[0].stats),
                        ws.format_nslit(st[0].stats, chancode, self.eventid),
                    ]
                )
                self.workspace.insert_aux(
                    xmlstr,
                    "StationMetrics",
                    metricpath,
                    overwrite=self.gmrecords.args.overwrite,
                )
        logging.info(
            "Added station metrics to workspace files with tag "
            f"'{self.gmrecords.args.label}'."
        )

        self.workspace.close()
        return event.id

    def _get_ps2ff(self, event):
        self.rrup_interp, self.rjb_interp = get_ps2ff_interpolation(event)
