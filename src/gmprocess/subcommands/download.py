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
event_utils = LazyLoader("event_utils", globals(), "gmprocess.utils.event_utils")


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
        self._get_events()

        logging.info(f"Number of events to download: {len(self.events)}.")
        nevents = len(self.events)
        for i, event in enumerate(self.events):
            logging.info(
                f"Downloading waveforms for event {event.id} ({i+1} of {nevents})..."
            )
            event_dir = gmrecords.data_path / event.id
            event_dir.mkdir(exist_ok=True)

            download_utils.download_waveforms(
                event=event, event_dir=event_dir, config=copy.deepcopy(gmrecords.conf)
            )

    def _get_events(self):
        """Get event information, downloading event information from ComCat if only event ids are provided.

        Order of precedence:
            1. List of ComCat event ids (details downloaded from ComCat)
            2. CSV file with ComCat event ids (details downloaded from ComCat) or event information.
        """
        data_dir = self.gmrecords.data_path
        data_dir.mkdir(parents=True, exist_ok=True)

        event_ids = [ev_id.strip() for ev_id in self.gmrecords.args.eventid.split(",")]
        if event_ids:
            events = self._download_events(event_ids)
        elif self.gmrecords.args.textfile:
            events_filename = pathlib.Path(self.gmrecords.args.textfile)
            if not events_filename.is_file():
                raise IOError(
                    f"Could not find events file `{events_filename}` to read events information."
                )
            events_info = event_utils.parse_events_file(events_filename)
            if len(events_info) and isinstance(events_info[0], event_utils.ScalarEvent):
                # Events file contains events information.
                events = events_info
            else:
                # Events file contains just event ids.
                events = self._download_events(events_info)
        else:
            raise ValueError("No events specified.")

        self._write_events(events, data_dir)

    def _download_events(self, event_ids):
        events = []
        for event_id in event_ids:
            data = download_utils.download_comcat_event(event_id)
            download_utils.write_event_geojson(data)
            event = event.ScalarEvent.from_json(data)

            # If the event ID has been updated, issue a warning to the user
            if event.id != event_id:
                logging.warn(
                    f"Found updated event id in event information. {event_id} -> {event.id}"
                )

            if event:
                events.append(event)

        return events

    def _write_events(self, events, data_dir):
        for event in events:
            event_dir = data_dir / event.id
            event_dir.mkdir(parents=True, exist_ok=True)
            download_utils.create_event_file(event, event_dir)
