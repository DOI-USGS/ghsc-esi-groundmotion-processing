"""Module for ExportProvenanceTablesModule class."""

import logging

from gmprocess.subcommands.lazy_loader import LazyLoader

arg_dicts = LazyLoader("arg_dicts", globals(), "gmprocess.subcommands.arg_dicts")
base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
constants = LazyLoader("constants", globals(), "gmprocess.utils.constants")
scalar_event = LazyLoader("scalar_event", globals(), "gmprocess.core.scalar_event")


class ExportProvenanceTablesModule(base.SubcommandModule):
    """Export provenance tables."""

    command_name = "export_provenance_tables"
    aliases = ("ptables",)

    arguments = [
        arg_dicts.ARG_DICTS["output_format"],
    ]

    def main(self, gmrecords):
        """Export provenance tables.

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
                f"Creating provenance tables for event {event_id} "
                f"({1+ievent} of {len(event_ids)})..."
            )
            event_dir = gmrecords.data_path / event_id

            self.open_workspace(event_id)
            if not self.workspace:
                continue
            self._get_pstreams(event_id)

            if not (hasattr(self, "pstreams") and len(self.pstreams) > 0):
                logging.info(
                    "No processed waveforms available. No provenance tables created."
                )
                self.close_workspace()
                continue

            provdata = self.workspace.get_provenance(
                event_id, labels=self.gmrecords.args.label
            )
            self.close_workspace()

            basename = f"{gmrecords.project_name}_{gmrecords.args.label}_provenance"
            if gmrecords.args.output_format == "csv":
                csvfile = event_dir / f"{basename}.csv"
                self.append_file("Provenance", csvfile)
                provdata.to_csv(csvfile, index=False)
            else:
                excelfile = event_dir / f"{basename}.xlsx"
                self.append_file("Provenance", excelfile)
                provdata.to_excel(excelfile, index=False)

        self._summarize_files_created()
