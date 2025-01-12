"""Module for the ProcessWaveformsModule class."""

import logging
from concurrent.futures import ProcessPoolExecutor

from gmprocess.subcommands.lazy_loader import LazyLoader

base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
constants = LazyLoader("constants", globals(), "gmprocess.utils.constants")
scalar_event = LazyLoader("scalar_event", globals(), "gmprocess.core.scalar_event")
processing = LazyLoader(
    "processing", globals(), "gmprocess.waveform_processing.processing"
)


class ProcessWaveformsModule(base.SubcommandModule):
    """Process waveform data."""

    command_name = "process_waveforms"
    aliases = ("process",)

    # Note: do not use the ARG_DICT entry for label because the explanation is
    # different here.
    arguments = [
        {
            "short_flag": "-r",
            "long_flag": "--reprocess",
            "help": "Reprocess data using manually review information.",
            "default": False,
            "action": "store_true",
        },
    ]

    def main(self, gmrecords):
        """Process data using steps defined in configuration file.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info(f"Running subcommand '{self.command_name}'")

        self.gmrecords = gmrecords
        self._check_arguments()

        event_ids, _ = self._get_event_ids_from_args()
        logging.info(f"Number of events to process: {len(event_ids)}")

        # get the process tag from the user or use "default" for tag
        self.process_tag = gmrecords.args.label or "default"
        logging.info(f"Processing tag: {self.process_tag}")

        for ievent, event_id in enumerate(event_ids):
            logging.info(
                f"Processing waveforms for event {event_id} "
                f"({1+ievent} of {len(event_ids)})..."
            )
            self._process_event(event_id)

        self._summarize_files_created()

    def _process_event(self, event_id):
        self.open_workspace(event_id)
        if self.workspace is None:
            return
        ds = self.workspace.dataset
        station_list = ds.waveforms.list()
        event = self.workspace.get_event(event_id)
        strec = self.workspace.get_strec(event_id)

        processed_streams = []
        if self.gmrecords.args.num_processes:
            futures = []
            executor = ProcessPoolExecutor(
                max_workers=self.gmrecords.args.num_processes
            )

        if self.gmrecords.args.reprocess:
            process_type = "Reprocessing"
            plabel = self.process_tag
        else:
            process_type = "Processing"
            plabel = "unprocessed"
        logging.info(f"{process_type} '{plabel}' streams for event {event_id}...")

        for station_id in station_list:
            # Cannot parallelize IO to ASDF file
            config = self._get_config()
            raw_streams = self.workspace.get_streams(
                event_id,
                stations=[station_id],
                labels=["unprocessed"],
                config=config,
            )
            if self.gmrecords.args.reprocess:
                # Don't use "processed_streams" variable name because that is what is
                # being used for the result of THIS round of processing; thus, I'm
                # using "old_streams" for the previously processed streams which
                # contain the manually reviewed information
                old_streams = self.workspace.get_streams(
                    event_id,
                    stations=[station_id],
                    labels=[self.process_tag],
                    config=config,
                )
            else:
                old_streams = None

            if len(raw_streams):
                if self.gmrecords.args.num_processes:
                    future = executor.submit(
                        processing.process_streams,
                        raw_streams,
                        event,
                        config,
                        old_streams,
                        strec,
                    )
                    futures.append(future)
                else:
                    processed_streams.append(
                        processing.process_streams(
                            raw_streams, event, config, old_streams, strec
                        )
                    )

        if self.gmrecords.args.num_processes:
            # Collect the processed streams
            processed_streams = [future.result() for future in futures]
            executor.shutdown()

        # Note: cannot parallelize IO to ASDF file

        overwrite = self.gmrecords.args.overwrite
        if self.gmrecords.args.reprocess:
            overwrite = True

        for processed_stream in processed_streams:
            self.workspace.add_streams(
                event,
                processed_stream,
                label=self.process_tag,
                gmprocess_version=self.gmrecords.gmprocess_version,
                overwrite=overwrite,
            )

        self.close_workspace()
        return event_id
