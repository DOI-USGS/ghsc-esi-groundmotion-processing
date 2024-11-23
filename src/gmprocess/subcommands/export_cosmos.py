#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import pathlib

from gmprocess.io.cosmos.cosmos_writer import Volume
from gmprocess.subcommands.lazy_loader import LazyLoader

arg_dicts = LazyLoader("arg_dicts", globals(), "gmprocess.subcommands.arg_dicts")
base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
ws = LazyLoader("ws", globals(), "gmprocess.io.asdf.stream_workspace")
const = LazyLoader("const", globals(), "gmprocess.utils.constants")
cosmos = LazyLoader("cosmos", globals(), "gmprocess.io.cosmos.cosmos_writer")
confmod = LazyLoader("confmod", globals(), "gmprocess.utils.config")

VOLUMES = {
    "RAW": Volume.RAW,
    "CONVERTED": Volume.CONVERTED,
    "PROCESSED": Volume.PROCESSED,
    "SPECTRA": Volume.SPECTRA,
}


class ExportCosmosModule(base.SubcommandModule):
    """Export COSMOS format files."""

    command_name = "export_cosmos"
    aliases = ("cosmos",)

    # arguments = []
    arguments = [
        {
            "short_flag": "-f",
            "long_flag": "--output-folder",
            "help": (
                "Choose output folder for COSMOS files. "
                "Default is existing event folder."
            ),
            "default": None,
        },
        {
            "short_flag": "-s",
            "long_flag": "--separate-channels",
            "help": (
                "Turn off concatenation of COSMOS text files. "
                "Default is to concatenate all channels from a stream into one file."
                "Setting this flag will result in one file per channel."
            ),
            "default": False,
        },
        {
            "short_flag": "-p",
            "long_flag": "--process-level",
            "help": (
                "Select the volume or processing level to output. "
                "OPTIONS are [RAW,CONVERTED,PROCESSED, SPECTRA] (V0,V1,V2,V3 in Cosmos parlance)."
            ),
            "default": "RAW",
        },
        {
            "long_flag": "--label",
            "help": (
                "Specify the processing desired processing label. Choosing -p RAW "
                "will automatically use the 'unprocessed' label. If there is only "
                "one label for processed data, then that one will be automatically "
                "chosen when -p PROCESSED is selected."
            ),
            "default": None,
        },
    ]

    def main(self, gmrecords):
        """Export COSMOS format files.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info(f"Running subcommand '{self.command_name}'")

        self.gmrecords = gmrecords
        self._check_arguments()
        event_ids, events = self._get_event_ids_from_args()

        if events:
            logging.critical(
                "autoprocess subcommand only works with events given as ComCat ids."
            )
        nevents = 0
        nstreams = 0
        ntraces = 0
        self.files_created = {"cosmos_files": []}
        for ievent, event_id in enumerate(event_ids):
            logging.info(
                f"Creating COSMOS files for event {event_id} "
                f"({1+ievent} of {len(event_ids)})..."
            )
            event_dir = gmrecords.data_path / event_id
            output_dir = event_dir / "cosmos"
            if self.gmrecords.args.output_folder is not None:
                output_dir = pathlib.Path(self.gmrecords.args.output_folder)
            if not output_dir.exists():
                output_dir.mkdir(parents=True)
            workname = event_dir / const.WORKSPACE_NAME
            if not workname.is_file():
                logging.info(
                    f"No workspace file found for event {event_id}. Please run "
                    "subcommand 'assemble' to generate workspace file."
                )
                logging.info("Continuing to next event.")
                continue
            # we will ask for volume and label options in the future
            volume_str = gmrecords.args.process_level
            if volume_str not in VOLUMES:
                raise KeyError(
                    f"Unknown process level {volume_str}. Choose from {VOLUMES.keys()}"
                )
            volume = VOLUMES[volume_str]

            concatenate_channels = not gmrecords.args.separate_channels
            # create a
            cosmos_writer = cosmos.CosmosWriter(
                output_dir,
                workname,
                volume=volume,
                concatenate_channels=concatenate_channels,
            )
            logging.info(f"Processing event {event_id}...")
            tfiles, tnevents, tnstreams, tntraces = cosmos_writer.write()
            nevents += tnevents
            nstreams += tnstreams
            ntraces += tntraces
            self.files_created["cosmos_files"] += tfiles
        logging.info(
            f"Processed {nevents} events - {nstreams} streams and {ntraces} traces."
        )
        self._summarize_files_created()
