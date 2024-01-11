"""Module for GenerateHTMLMapModule class."""

import logging

from gmprocess.subcommands.lazy_loader import LazyLoader

base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
constants = LazyLoader("constants", globals(), "gmprocess.utils.constants")
report_utils = LazyLoader("report_utils", globals(), "gmprocess.utils.report_utils")
scalar_event = LazyLoader("scalar_event", globals(), "gmprocess.core.scalar_event")


class GenerateHTMLMapModule(base.SubcommandModule):
    """Generate interactive station maps."""

    command_name = "generate_station_maps"
    aliases = ("maps",)

    arguments = []

    def main(self, gmrecords):
        """Generate summary report.

        This function generates station map.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info(f"Running subcommand '{self.command_name}'")

        self.gmrecords = gmrecords
        self._check_arguments()
        event_ids, _ = self._get_event_ids_from_args()

        for ievent, event_id in enumerate(event_ids):
            event_dir = self.gmrecords.data_path / event_id

            self.open_workspace(event_id)
            if not self.workspace:
                continue
            ds = self.workspace.dataset
            station_list = ds.waveforms.list()
            if len(station_list) == 0:
                logging.info("No processed waveforms available. No report generated.")
                continue

            self._get_labels()
            config = self.workspace.config
            logging.info(
                f"Generating station maps for event {event_id} "
                f"({1+ievent} of {len(event_ids)})..."
            )

            pstreams = []
            for station_id in station_list:
                streams = self.workspace.get_streams(
                    event_id,
                    stations=[station_id],
                    labels=[self.gmrecords.args.label],
                    config=config,
                )
                if not len(streams):
                    logging.error(
                        f"No matching streams found for {station_id} for {event_id}."
                    )
                    continue

                for stream in streams:
                    pstreams.append(stream)

            event = self.workspace.get_event(event_id)
            self.close_workspace()

            mapfile = report_utils.draw_stations_map(pstreams, event, event_dir)
            self.append_file("Station map", mapfile)

        self._summarize_files_created()
