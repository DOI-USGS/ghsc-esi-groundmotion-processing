"""Module for DownloadModule."""

import logging
import copy
import sys

import obspy

#  test functions thoroughly before merging
from gmprocess.subcommands.lazy_loader import LazyLoader

arg_dicts = LazyLoader("arg_dicts", globals(), "gmprocess.subcommands.arg_dicts")
base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
constants = LazyLoader("constants", globals(), "gmprocess.utils.constants")
misc = LazyLoader("misc", globals(), "gmprocess.utils.misc")
global_fetcher = LazyLoader("global_fetcher", globals(), "gmprocess.io.global_fetcher")

download_utils = LazyLoader(
    "download_utils", globals(), "gmprocess.utils.download_utils"
)
scalar_event = LazyLoader("scalar_event", globals(), "gmprocess.core.scalar_event")


class DownloadModule(base.SubcommandModule):
    """Download data and organize it in the project data directory."""

    command_name = "download"

    arguments = [
        {
            "short_flag": "-r",
            "long_flag": "--rupture",
            "help": "Get only rupture.json.",
            "default": False,
            "action": "store_true",
        },
        {
            "short_flag": "-s",
            "long_flag": "--strec",
            "help": "Get strec.json.",
            "default": False,
            "action": "store_true",
        },
        {
            "short_flag": "-o",
            "long_flag": "--origin",
            "help": "Get event.json.",
            "default": False,
            "action": "store_true",
        },
        {
            "short_flag": "-w",
            "long_flag": "--waveforms",
            "help": "Get only waveforms.",
            "default": False,
            "action": "store_true",
        },
    ]
    epilog = (
        "Note that in order to download strec, rupture, waveforms the origin "
        "is required. So the origin will be downloaded when these are "
        "requested."
    )

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

        event_ids, events = self._get_event_ids_from_args()
        logging.info(f"Number of events to assemble: {len(event_ids)}")
        download_all = (
            (gmrecords.args.rupture is False)
            and (gmrecords.args.origin is False)
            and (gmrecords.args.strec is False)
            and (gmrecords.args.waveforms is False)
        )

        for ievent, event_id in enumerate(event_ids):
            event_dir = gmrecords.data_path / event_id
            event_dir.mkdir(exist_ok=True)
            if (events is None) or (not events[ievent]):
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

            if (not download_all) and gmrecords.args.origin:
                continue

            config = copy.deepcopy(gmrecords.conf)

            if download_all or gmrecords.args.rupture:
                # this uses download_comcat_event again!!
                download_utils.download_rupture_file(event.id, event_dir)

            strec = None
            if gmrecords.args.strec and not config["strec"]["enabled"]:
                print("strec is not enabled, please enable and try again.")
                sys.exit(0)

            if config["strec"]["enabled"] and (download_all or gmrecords.args.strec):
                strec = download_utils.get_strec_results(event, event_dir)

            if download_all or gmrecords.args.waveforms:
                # Make raw directory
                rawdir = misc.get_rawdir(event_dir)
                logging.info(
                    f"Downloading waveforms for event {event_id} ({ievent+1} of {len(event_ids)})..."
                )
                global_fetcher.fetch_data(
                    event.time.datetime,
                    event.latitude,
                    event.longitude,
                    event.depth_km,
                    event.magnitude,
                    config=config,
                    rawdir=rawdir,
                    stream_collection=False,
                    strec=strec,
                )
