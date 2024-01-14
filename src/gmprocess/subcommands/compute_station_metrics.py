"""Module for ComputeStationMetricsModule class."""

import logging
import pathlib

from gmprocess.subcommands.lazy_loader import LazyLoader

origin = LazyLoader("origin", globals(), "esi_utils_rupture.origin")

arg_dicts = LazyLoader("arg_dicts", globals(), "gmprocess.subcommands.arg_dicts")
base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
constants = LazyLoader("constants", globals(), "gmprocess.utils.constants")
scalar_event = LazyLoader("scalar_event", globals(), "gmprocess.core.scalar_event")
rupture_utils = LazyLoader("rupture_utils", globals(), "gmprocess.utils.rupture_utils")
sta_collection = LazyLoader(
    "sta_collection", globals(), "gmprocess.metrics.station_metric_collection"
)
sta_xml = LazyLoader("sta_xml", globals(), "gmprocess.io.asdf.station_metrics_xml")

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
        event_ids, _ = self._get_event_ids_from_args()

        for ievent, event_id in enumerate(event_ids):
            logging.info(
                "Computing station metrics for event %s (%s of %s)...",
                event_id,
                1 + ievent,
                len(event_ids),
            )
            self._event_station_metrics(event_id)

        self._summarize_files_created()

    def _event_station_metrics(self, event_id):
        self.open_workspace(event_id)
        if not self.workspace:
            return

        ds = self.workspace.dataset
        self._get_labels()
        config = self._get_config()
        event = self.workspace.get_event(event_id)

        station_list = ds.waveforms.list()
        if not len(station_list):
            self.close_workspace()
            return

        event_dir = self.gmrecords.data_path / event.id
        rupture_filename = rupture_utils.get_rupture_filename(event_dir)
        origin_obj = origin.Origin(
            {
                "id": event.id,
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

        if isinstance(rupture_filename, pathlib.Path):
            rupture_filename = str(rupture_filename)

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
                    [stream], event, config, rupture_file=rupture_filename
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

        self.close_workspace()
