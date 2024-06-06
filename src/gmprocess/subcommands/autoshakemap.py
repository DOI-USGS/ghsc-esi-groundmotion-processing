"""Module for AutoShakemapModule class."""

import logging

from gmprocess.subcommands.lazy_loader import LazyLoader

arg_dicts = LazyLoader("arg_dicts", globals(), "gmprocess.subcommands.arg_dicts")
base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
scalar_event = LazyLoader("scalar_event", globals(), "gmprocess.core.scalar_event")
download = LazyLoader("download", globals(), "gmprocess.subcommands.download")
import_data = LazyLoader("import_data", globals(), "gmprocess.subcommands.import_data")
assemble = LazyLoader("assemble", globals(), "gmprocess.subcommands.assemble")
process_waveforms = LazyLoader(
    "process_waveforms", globals(), "gmprocess.subcommands.process_waveforms"
)
compute_station_metrics = LazyLoader(
    "compute_station_metrics",
    globals(),
    "gmprocess.subcommands.compute_station_metrics",
)
compute_waveform_metrics = LazyLoader(
    "compute_waveform_metrics",
    globals(),
    "gmprocess.subcommands.compute_waveform_metrics",
)
export_metric_tables = LazyLoader(
    "export_metric_tables", globals(), "gmprocess.subcommands.export_metric_tables"
)
export_gmpacket = LazyLoader(
    "export_gmpacket", globals(), "gmprocess.subcommands.export_gmpacket"
)
generate_regression_plot = LazyLoader(
    "generate_regression_plot",
    globals(),
    "gmprocess.subcommands.generate_regression_plot",
)
generate_report = LazyLoader(
    "generate_report", globals(), "gmprocess.subcommands.generate_report"
)


class AutoShakemapModule(base.SubcommandModule):
    """Chain together subcommands to get shakemap ground motion file."""

    command_name = "autoshakemap"

    arguments = [
        {
            "short_flag": "-p",
            "long_flag": "--path",
            "help": (
                "Path to external data file or directory. If given, "
                "then the download step is also skipped."
            ),
            "type": str,
            "default": None,
        },
        {
            "long_flag": "--skip-download",
            "help": "Skip data download step.",
            "default": False,
            "action": "store_true",
        },
        {
            "short_flag": "-d",
            "long_flag": "--diagnostics",
            "help": (
                "Include diagnostic outputs that are created after "
                "ShakeMap data file is created."
            ),
            "default": False,
            "action": "store_true",
        },
    ]

    def main(self, gmrecords):
        """Chain together subcommands to get shakemap ground motion file."""
        logging.info(f"Running subcommand '{self.command_name}'")
        self.gmrecords = gmrecords
        self._check_arguments()

        # Hard code overwrite to True since this is all meant to run end-to-end
        # without interruption.
        gmrecords.args.overwrite = True

        event_ids, events = self._get_event_ids_from_args()
        if events:
            logging.critical(
                "autoshakemap subcommand only works with events given as ComCat ids."
            )

        for ievent, event_id in enumerate(event_ids):
            logging.info(
                f"(auto)processing event {event_id} ({1+ievent} of {len(event_ids)})..."
            )
            # stomp on gmrecords.args.event_id
            gmrecords.args.event_id = [event_id]

            # Chain together relevant subcommand modules:
            if (not gmrecords.args.skip_download) and (gmrecords.args.path is None):
                download.DownloadModule().main(gmrecords)

            if gmrecords.args.path is not None:
                import_data.ImportModule().main(gmrecords)

            assemble.AssembleModule().main(gmrecords)
            process_waveforms.ProcessWaveformsModule().main(gmrecords)
            compute_station_metrics.ComputeStationMetricsModule().main(gmrecords)
            compute_waveform_metrics.ComputeWaveformMetricsModule().main(gmrecords)
            export_gmpacket.ExportGMPacketModule().main(gmrecords)

            if gmrecords.args.diagnostics:
                export_metric_tables.ExportMetricTablesModule().main(gmrecords)
                generate_regression_plot.GenerateRegressionPlotModule().main(gmrecords)
                generate_report.GenerateReportModule().main(gmrecords)
