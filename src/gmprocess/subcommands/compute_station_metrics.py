"""Module for ComputeStationMetricsModule class."""

import logging
import pathlib

from gmprocess.subcommands.lazy_loader import LazyLoader

arg_dicts = LazyLoader("arg_dicts", globals(), "gmprocess.subcommands.arg_dicts")
base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
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

        event_dir = self.gmrecords.data_path / event_id
        rupture_filename = rupture_utils.get_rupture_filename(event_dir)

        if isinstance(rupture_filename, pathlib.Path):
            rupture_filename = str(rupture_filename)

        # for station_id in station_list:
        streams = self.workspace.get_streams(
            event_id,
            labels=[self.gmrecords.args.label],
            config=config,
        )
        if not streams:
            logging.error(
                "No matching streams found. Aborting computing station metrics."
            )
            return

        smc = sta_collection.StationMetricCollection.from_streams(
            streams, event, config, rupture_file=rupture_filename
        )
        for i, sm in enumerate(smc.station_metrics):

            # check station stream passed QA check
            names = smc.stream_paths[i].split("/")[1].split(".")
            station_stream = streams.select(
                network=names[0], station=names[1], instrument=names[3][0:2]
            )
            for st in station_stream:
                if not st.passed:
                    break
            else:
                station_xml = sta_xml.StationMetricsXML(sm)
                xmlstr = station_xml.to_xml()
                self.workspace.insert_aux(
                    xmlstr,
                    "StationMetrics",
                    smc.stream_paths[i],
                    overwrite=self.gmrecords.args.overwrite,
                )
            continue

        logging.info(
            "Added station metrics to workspace files with tag '%s'.",
            self.gmrecords.args.label,
        )

        self.close_workspace()
