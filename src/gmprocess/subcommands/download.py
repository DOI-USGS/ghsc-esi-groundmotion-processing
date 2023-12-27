"""Module for DownloadModule."""

import logging
import copy

import obspy

from gmprocess.subcommands.lazy_loader import LazyLoader

arg_dicts = LazyLoader("arg_dicts", globals(), "gmprocess.subcommands.arg_dicts")
base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
constants = LazyLoader("constants", globals(), "gmprocess.utils.constants")
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
                event_info = download_utils.download_comcat_event(event_id)
                scalar_event.write_geojson(event_info, event_dir)

                event = scalar_event.ScalarEvent.from_params(
                    id=event_info["id"],
                    time=obspy.UTCDateTime(event_info["properties"]["time"] / 1000.0),
                    latitude=event_info["geometry"]["coordinates"][1],
                    longitude=event_info["geometry"]["coordinates"][0],
                    depth_km=event_info["geometry"]["coordinates"][2],
                    magnitude=event_info["properties"]["mag"],
                    magnitude_type=event_info["properties"].get("magType", None),
                )
            else:
                event = events[ievent]
                event.to_json(event_dir)

            download_utils.download_event_data(
                event=event, event_dir=event_dir, config=copy.deepcopy(gmrecords.conf)
            )
