"""Module for ExportGMPacketModule class."""

import logging

from gmprocess.subcommands.lazy_loader import LazyLoader

arg_dicts = LazyLoader("arg_dicts", globals(), "gmprocess.subcommands.arg_dicts")
base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
ws = LazyLoader("ws", globals(), "gmprocess.io.asdf.stream_workspace")
const = LazyLoader("const", globals(), "gmprocess.utils.constants")
gmp_utils = LazyLoader("sm_utils", globals(), "gmprocess.utils.export_gmpacket_utils")
confmod = LazyLoader("confmod", globals(), "gmprocess.utils.config")


class ExportGMPacketModule(base.SubcommandModule):
    """Export JSON ground motion packet files."""

    command_name = "export_gmpacket"
    aliases = ("gmpacket",)

    arguments = []

    def main(self, gmrecords):
        """Export files for ShakeMap input.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info(f"Running subcommand '{self.command_name}'")

        self.gmrecords = gmrecords
        self._check_arguments()
        self._get_events()

        for ievent, event in enumerate(self.events):
            self.eventid = event.id
            logging.info(
                f"Creating ground-motion-packet files for event {self.eventid} "
                f"({1+ievent} of {len(self.events)})..."
            )

            event_dir = gmrecords.data_path / event.id
            workname = event_dir / const.WORKSPACE_NAME
            if not workname.is_file():
                logging.info(
                    f"No workspace file found for event {event.id}. Please run "
                    "subcommand 'assemble' to generate workspace file."
                )
                logging.info("Continuing to next event.")
                continue

            packet_writer = gmp_utils.GroundMotionPacketWriter(
                event_dir, workname, label="default"
            )
            files, nevents, nstreams, ntraces = packet_writer.write()
            logging.info(
                f"Processed {nevents} events - {nstreams} streams and {ntraces} traces."
            )
            if len(files):
                jsonfile = files[0]
                self.append_file("shakemap", jsonfile)

        self._summarize_files_created()
