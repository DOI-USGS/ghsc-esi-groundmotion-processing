"""Module for GenerateReportModule class."""

import logging
import shutil
from concurrent.futures import ProcessPoolExecutor

from tqdm import tqdm

from gmprocess.subcommands.lazy_loader import LazyLoader


base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
report = LazyLoader("report", globals(), "gmprocess.io.report")
splot = LazyLoader("plot", globals(), "gmprocess.utils.summary_plots")
mplot = LazyLoader("plot", globals(), "gmprocess.utils.misc_plots")
constants = LazyLoader("constants", globals(), "gmprocess.utils.constants")
scalar_event = LazyLoader("scalar_event", globals(), "gmprocess.core.scalar_event")


class GenerateReportModule(base.SubcommandModule):
    """Generate summary report (latex required)."""

    command_name = "generate_report"
    aliases = ("report",)

    arguments = []

    def main(self, gmrecords):
        """Generate summary report.

        This function generates summary plots and then combines them into a
        report with latex. If latex (specifically `pdflatex`) is not found on
        the system then the PDF report will not be generated but the
        constituent plots will be available.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info(f"Running subcommand '{self.command_name}'")

        self.gmrecords = gmrecords
        self._check_arguments()
        event_ids, _ = self._get_event_ids_from_args()

        for ievent, event_id in enumerate(event_ids):
            event_dir = self.gmrecords.data_path / event_id
            try:
                event = scalar_event.ScalarEvent.from_workspace(
                    event_dir / constants.WORKSPACE_NAME
                )
            except FileNotFoundError:
                logging.info(
                    f"No workspace.h5 file found for event {event_id}. Skipping..."
                )
                continue

            config = self._get_config()
            pstreams = self.generate_diagnostic_plots(event, config)
            if pstreams is None:
                return

            logging.info(
                f"Generating summary report for event {event_id} "
                f"({1+ievent} of {len(event_ids)})..."
            )

            build_conf = config["build_report"]
            if build_conf["enabled"]:
                report_format = build_conf["format"]
                if report_format == "latex":
                    report_file, success = report.build_report_latex(
                        pstreams,
                        event_dir,
                        event,
                        prefix=f"{gmrecords.project_name}_{gmrecords.args.label}",
                        config=config,
                        gmprocess_version=gmrecords.gmprocess_version,
                    )
                else:
                    report_file = ""
                    success = False
                if report_file.is_file() and success:
                    self.append_file("Summary report", report_file)

        self._summarize_files_created()

    def generate_diagnostic_plots(self, event, config):
        self.open_workspace(event.id)
        if not self.workspace:
            return

        ds = self.workspace.dataset
        station_list = ds.waveforms.list()
        if len(station_list) == 0:
            logging.info("No processed waveforms available. No report generated.")
            return []

        self._get_labels()
        if self.gmrecords.args.num_processes:
            futures = []
            executor = ProcessPoolExecutor(
                max_workers=self.gmrecords.args.num_processes
            )

        logging.info(f"Creating diagnostic plots for event {event.id}...")
        event_dir = self.gmrecords.data_path / event.id
        plot_dir = event_dir / "plots"
        if plot_dir.exists():
            shutil.rmtree(plot_dir, ignore_errors=True)
        plot_dir.mkdir()

        results = []
        pstreams = []
        for station_id in tqdm(station_list):
            streams = self.workspace.get_streams(
                event.id,
                stations=[station_id],
                labels=[self.gmrecords.args.label],
                config=config,
            )
            if not len(streams):
                logging.info("No matching streams found. Cannot generate report.")
                return
            streams_raw = (
                self.workspace.get_streams(
                    event.id,
                    stations=[station_id],
                    labels=["unprocessed"],
                    config=config,
                )
                if "unprocessed" in self.workspace.get_labels()
                else None
            )

            for stream, stream_raw in zip(streams, streams_raw):
                pstreams.append(stream)
                if self.gmrecords.args.num_processes > 0:
                    future = executor.submit(
                        _summary_plot,
                        stream,
                        stream_raw,
                        plot_dir,
                        event,
                        config,
                    )
                    futures.append(future)
                else:
                    results.append(
                        _summary_plot(stream, stream_raw, plot_dir, event, config)
                    )

        if self.gmrecords.args.num_processes:
            # Collect the results??
            results = [future.result() for future in futures]
            executor.shutdown()

        self.close_workspace()

        return pstreams


def _summary_plot(stream, stream_raw, plot_dir, event, config):
    sp = splot.SummaryPlot(stream, stream_raw, plot_dir, event, config)
    return sp.plot()
