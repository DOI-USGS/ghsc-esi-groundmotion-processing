"""Module for ExportGMPacketModule class."""

import logging

from gmprocess.subcommands.lazy_loader import LazyLoader

base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
constants = LazyLoader("constants", globals(), "gmprocess.utils.constants")
gmp_utils = LazyLoader("sm_utils", globals(), "gmprocess.utils.export_gmpacket_utils")
scalar_event = LazyLoader("scalar_event", globals(), "gmprocess.core.scalar_event")


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
        event_ids, _ = self._get_event_ids_from_args()

        for ievent, event_id in enumerate(event_ids):
            logging.info(
                f"Creating ground-motion-packet files for event {event_id} "
                f"({1+ievent} of {len(event_ids)})..."
            )

            event_dir = gmrecords.data_path / event_id
            workname = event_dir / constants.WORKSPACE_NAME
            if not workname.is_file():
                logging.info(
                    f"No workspace file found for event {event_id}. Please run "
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
