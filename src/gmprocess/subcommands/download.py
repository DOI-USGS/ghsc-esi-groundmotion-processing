"""Module for DownloadModule."""

import logging
import copy
import pathlib

from gmprocess.subcommands.lazy_loader import LazyLoader

arg_dicts = LazyLoader("arg_dicts", globals(), "gmprocess.subcommands.arg_dicts")
base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
download_utils = LazyLoader(
    "download_utils", globals(), "gmprocess.utils.download_utils"
)
scalar_event = LazyLoader("scalar_event", globals(), "gmprocess.core.scalar_event")


class DownloadModule(base.SubcommandModule):
    """Download data and organize it in the project data directory."""

    command_name = "download"

    arguments = []

    def main(self, gmrecords):
        """
        Download data and organize it in the project data directory.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info(f"Running subcommand '{self.command_name}'...")
        self.gmrecords = gmrecords
        self._check_arguments()

        data_path = self.gmrecords.data_path
        user_ids = self.gmrecords.args.event_id
        events_filename = self.gmrecords.args.textfile
        file_ids, events = scalar_event.get_events_from_file(events_filename)
        event_ids = scalar_event.get_event_ids(
            ids=user_ids, file_ids=file_ids, data_dir=data_path
        )
        logging.info(f"Number of events to assemble: {len(event_ids)}")
        for ievent, event_id in enumerate(event_ids):
            logging.info(
                f"Downloading waveforms for event {event_id} ({ievent+1} of {len(event_ids)})..."
            )
            event_dir = gmrecords.data_path / event_id
            event_dir.mkdir(exist_ok=True)

            if not events:
                event_json = download_utils.download_comcat_event()
                event = scalar_event.ScalarEvent.from_json(event_json)
                scalar_event.write_geojson(event_json.event_dir)
            else:
                event = events[ievent]
                event.to_json(event_dir)

            download_utils.download_waveforms(
                event=event, event_dir=event_dir, config=copy.deepcopy(gmrecords.conf)
            )
