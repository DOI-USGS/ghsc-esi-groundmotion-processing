"""Module for ExportShakeMapModule class."""

import logging

from gmprocess.subcommands.lazy_loader import LazyLoader

arg_dicts = LazyLoader("arg_dicts", globals(), "gmprocess.subcommands.arg_dicts")
base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
constants = LazyLoader("constants", globals(), "gmprocess.utils.constants")
sm_utils = LazyLoader("sm_utils", globals(), "gmprocess.utils.export_shakemap_utils")
scalar_event = LazyLoader("scalar_event", globals(), "gmprocess.core.scalar_event")


class ExportShakeMapModule(base.SubcommandModule):
    """Export files for ShakeMap input."""

    command_name = "export_shakemap"
    aliases = ("shakemap",)

    arguments = [
        {
            "short_flag": "-x",
            "long_flag": "--expand-imts",
            "help": (
                "Use expanded IMTs. Currently this only means all the "
                "SA that have been computed, plus PGA and PGV (if "
                "computed). Could eventually expand for other IMTs also."
            ),
            "default": False,
            "action": "store_true",
        },
    ]

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
                f"Creating shakemap files for event {event_id} "
                f"({1+ievent} of {len(event_ids)})..."
            )

            self.open_workspace(event_id)
            if not self.workspace:
                continue
            self._get_labels()
            config = self._get_config()
            event_dir = gmrecords.data_path / event_id
            event = self.workspace.get_event(event_id)

            expanded_imts = self.gmrecords.args.expand_imts
            jsonfile, stationfile, _ = sm_utils.create_json(
                self.workspace,
                event,
                event_dir,
                self.gmrecords.args.label,
                config=config,
                expanded_imts=expanded_imts,
            )

            self.close_workspace()
            if jsonfile is not None:
                self.append_file("shakemap", jsonfile)
            if stationfile is not None:
                self.append_file("shakemap", stationfile)

        self._summarize_files_created()
