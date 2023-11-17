"""Module for ComputeStationMetricsModule class."""

import logging
import pathlib

from gmprocess.subcommands.lazy_loader import LazyLoader

np = LazyLoader("np", globals(), "numpy")
ob = LazyLoader("ob", globals(), "obspy.geodetics.base")
oqgeo = LazyLoader("oqgeo", globals(), "openquake.hazardlib.geo.geodetic")
origin = LazyLoader("rupt", globals(), "esi_utils_rupture.origin")

arg_dicts = LazyLoader("arg_dicts", globals(), "gmprocess.subcommands.arg_dicts")
base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
utils = LazyLoader("utils", globals(), "gmprocess.utils")
rupt_utils = LazyLoader("rupt_utils", globals(), "gmprocess.utils.rupture_utils")
ws = LazyLoader("ws", globals(), "gmprocess.io.asdf.stream_workspace")
sta_collection = LazyLoader(
    "sta_collection", globals(), "gmprocess.metrics.station_metric_collection"
)
sta_xml = LazyLoader("sta_xml", globals(), "gmprocess.io.asdf.station_metrics_xml")
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
        logging.info("Running subcommand '%s'", self.command_name)

        self.gmrecords = gmrecords
        self._check_arguments()
        self._get_events()

        for ievent, event in enumerate(self.events):
            logging.info(
                "Computing station metrics for event %s (%s of %s)...",
                event.id,
                1 + ievent,
                len(self.events),
            )
            self._event_station_metrics(event)

        self._summarize_files_created()

    def _event_station_metrics(self, event):
        self.eventid = event.id
        event_dir = self.gmrecords.data_path / self.eventid
        workname = event_dir / utils.constants.WORKSPACE_NAME
        if not workname.is_file():
            logging.info(
                "No workspace file found for event %s. Please run "
                "subcommand 'assemble' to generate workspace file.",
                self.eventid,
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
        origin_obj = origin.Origin(
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
        self.origin = origin_obj

        if isinstance(rupture_file, pathlib.Path):
            rupture_file = str(rupture_file)

        for station_id in station_list:
            streams = self.workspace.get_streams(
                event.id,
                stations=[station_id],
                labels=[self.gmrecords.args.label],
                config=config,
            )
            if not streams:
                logging.error(
                    "No matching streams found. Aborting computing station "
                    "metrics for %s for %s.",
                    station_id,
                    event.id,
                )
                continue

            for stream in streams:
                if not stream.passed:
                    continue

                smc = sta_collection.StationMetricCollection.from_streams(
                    [stream], event, config, rupture_file=rupture_file
                )
                # we know there is only one element in the station_metrics list because
                # we only gave it one stream.
                station_xml = sta_xml.StationMetricsXML(smc.station_metrics[0])
                xmlstr = station_xml.to_xml()
                self.workspace.insert_aux(
                    xmlstr,
                    "StationMetrics",
                    smc.stream_paths[0],
                    overwrite=self.gmrecords.args.overwrite,
                )
        logging.info(
            "Added station metrics to workspace files with tag '%s'.",
            self.gmrecords.args.label,
        )

        self.workspace.close()
        return event.id
