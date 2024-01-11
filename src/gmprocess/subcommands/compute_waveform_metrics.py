"""Module for ComputeWaveformMetricsModule class."""

import logging
from concurrent.futures import ProcessPoolExecutor

from gmprocess.subcommands.lazy_loader import LazyLoader

arg_dicts = LazyLoader("arg_dicts", globals(), "gmprocess.subcommands.arg_dicts")
base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
constants = LazyLoader("constants", globals(), "gmprocess.utils.constants")
scalar_event = LazyLoader("scalar_event", globals(), "gmprocess.core.scalar_event")
path_utils = LazyLoader("path_utils", globals(), "gmprocess.io.asdf.path_utils")
wf_collection = LazyLoader(
    "wf_collection", globals(), "gmprocess.metrics.waveform_metric_collection"
)
wf_xml = LazyLoader("wf_xml", globals(), "gmprocess.io.asdf.waveform_metrics_xml")


class ComputeWaveformMetricsModule(base.SubcommandModule):
    """Compute waveform metrics."""

    command_name = "compute_waveform_metrics"
    aliases = ("wm",)

    arguments = []

    def main(self, gmrecords):
        """Compute waveform metrics.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info("Running subcommand '%s'", self.command_name)

        self.gmrecords = gmrecords
        self._check_arguments()
        event_ids, _ = self._get_event_ids_from_args()

        for ievent, event_id in enumerate(event_ids):
            logging.info(
                "Computing waveform metrics for event %s (%s of %s)...",
                event_id,
                1 + ievent,
                len(event_ids),
            )
            self._compute_event_waveform_metrics(event_id)

        self._summarize_files_created()

    def _compute_event_waveform_metrics(self, event_id):
        self.open_workspace(event_id)
        if not self.workspace:
            return

        ds = self.workspace.dataset
        station_list = ds.waveforms.list()
        self._get_labels()
        config = self._get_config()
        event = self.workspace.get_event(event_id)

        # Start with an empty metric_collection and we will append to it.
        metric_collection = wf_collection.WaveformMetricCollection()

        if self.gmrecords.args.num_processes:
            futures = []
            executor = ProcessPoolExecutor(
                max_workers=self.gmrecords.args.num_processes
            )

        for station_id in station_list:
            # Cannot parallelize IO to ASDF file
            streams = self.workspace.get_streams(
                event_id,
                stations=[station_id],
                labels=[self.gmrecords.args.label],
                config=config,
            )
            if not streams:
                logging.warning(
                    "No matching streams found. Aborting computation of station "
                    "metrics for %s for %s.",
                    station_id,
                    event_id,
                )
                continue

            for stream in streams:
                if not stream.passed:
                    continue

                logging.info("Calculating waveform metrics for %s...", stream.get_id())

                if self.gmrecords.args.num_processes > 0:
                    future = executor.submit(
                        wf_collection.WaveformMetricCollection.from_streams,
                        streams=[stream],
                        event=event,
                        config=config,
                        label=self.gmrecords.args.label,
                    )
                    futures.append(future)
                else:
                    metric_collection.append(
                        wf_collection.WaveformMetricCollection.from_streams(
                            [stream], event, config, self.gmrecords.args.label
                        )
                    )

        if self.gmrecords.args.num_processes:
            # Collect the processed streams
            metric_collections = [future.result() for future in futures]
            for met_col in metric_collections:
                metric_collection.append(met_col)
            executor.shutdown()

        # Cannot parallelize IO to ASDF file
        logging.info(
            "Adding waveform metrics to workspace files with tag '%s'.",
            self.gmrecords.args.label,
        )

        for waveform_metric, metric_path in zip(
            metric_collection.waveform_metrics,
            metric_collection.stream_paths,
        ):
            metric_xml = wf_xml.WaveformMetricsXML(waveform_metric.metric_list)
            xmlstr = metric_xml.to_xml()
            self.workspace.insert_aux(
                xmlstr,
                "WaveFormMetrics",
                metric_path,
                overwrite=self.gmrecords.args.overwrite,
            )

        self.workspace.close()
