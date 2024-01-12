"""Module for ExportFailureTablesModule class."""

import logging

from gmprocess.subcommands.lazy_loader import LazyLoader

pd = LazyLoader("pd", globals(), "pandas")

arg_dicts = LazyLoader("arg_dicts", globals(), "gmprocess.subcommands.arg_dicts")
base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
constants = LazyLoader("constants", globals(), "gmprocess.utils.constants")
scalar_event = LazyLoader("scalar_event", globals(), "gmprocess.core.scalar_event")


class ExportFailureTablesModule(base.SubcommandModule):
    """Export failure tables."""

    command_name = "export_failure_tables"
    aliases = ("ftables",)

    arguments = [
        {
            "long_flag": "--type",
            "help": (
                'Output failure information, either in short form ("short"),'
                'long form ("long"), or network form ("net"). short: Two '
                'column table, where the columns are "failure reason" and '
                '"number of records". net: Three column table where the '
                'columns are "network", "number passed", and "number failed". '
                'long: Two column table, where columns are "station ID" and '
                '"status" where status is "passed" or "failed" (with reason).'
            ),
            "type": str,
            "default": "short",
            "choices": ["short", "long", "net"],
        },
        arg_dicts.ARG_DICTS["output_format"],
        {
            "short_flag": "-l",
            "long_flag": "--log-status",
            "help": ("Include failure information in INFO logging."),
            "action": "store_true",
            "default": False,
        },
    ]

    def main(self, gmrecords):
        """Export failure tables.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info(f"Running subcommand '{self.command_name}'")

        self.gmrecords = gmrecords
        self._check_arguments()
        event_ids, _ = self._get_event_ids_from_args()

        failures = {}
        for ievent, event_id in enumerate(event_ids):
            logging.info(
                f"Creating failure tables for event {event_id} "
                f"({1+ievent} of {len(event_ids)})..."
            )

            self.open_workspace(event_id)
            if not self.workspace:
                continue

            self._get_pstreams(event_id)
            self.close_workspace()

            if not (hasattr(self, "pstreams") and len(self.pstreams) > 0):
                logging.info(
                    "No processed waveforms available. No failure tables created."
                )
                continue

            status_info = self.pstreams.get_status(self.gmrecords.args.type)
            failures[event_id] = status_info

            base_file_name = (
                f"{gmrecords.project_name}_{gmrecords.args.label}_"
                f"failure_reasons_{self.gmrecords.args.type}"
            )

            event_dir = gmrecords.data_path / event_id
            if self.gmrecords.args.output_format == "csv":
                csvfile = base_file_name + ".csv"
                csvpath = event_dir / csvfile
                self.append_file("Failure table", csvpath)
                status_info.to_csv(csvpath)
            else:
                excelfile = base_file_name + ".xlsx"
                excelpath = event_dir / excelfile
                self.append_file("Failure table", excelpath)
                status_info.to_excel(excelpath)

        if failures:
            comp_failures_path = self.gmrecords.data_path / (
                f"{gmrecords.project_name}_{gmrecords.args.label}_complete_failures.csv"
            )

            if self.gmrecords.args.type == "long":
                for idx, item in enumerate(failures.items()):
                    eqid, status = item
                    status = pd.DataFrame(status)
                    status["EarthquakeId"] = eqid
                    if idx == 0:
                        status.to_csv(comp_failures_path, mode="w")
                    else:
                        status.to_csv(comp_failures_path, mode="a", header=False)
            else:
                df_failures = pd.concat(failures.values())
                df_failures = df_failures.groupby(df_failures.index).sum()
                df_failures.to_csv(comp_failures_path)
            self.append_file("Complete failures", comp_failures_path)

            if self.gmrecords.args.log_status:
                logging.info(str(status_info))

        self._summarize_files_created()
