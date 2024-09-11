"""Module for AssembleModule class."""

import logging
from concurrent.futures import ProcessPoolExecutor

from gmprocess.subcommands.lazy_loader import LazyLoader

arg_dicts = LazyLoader("arg_dicts", globals(), "gmprocess.subcommands.arg_dicts")
base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
constants = LazyLoader("constants", globals(), "gmprocess.utils.constants")
scalar_event = LazyLoader("scalar_event", globals(), "gmprocess.core.scalar_event")
assemble_utils = LazyLoader(
    "assemble_utils", globals(), "gmprocess.utils.assemble_utils"
)


class AssembleModule(base.SubcommandModule):
    """Assemble raw data and organize it into an ASDF file."""

    command_name = "assemble"

    arguments = []

    def main(self, gmrecords):
        """
        Assemble data and organize it into an ASDF file.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info(f"Running subcommand '{self.command_name}'")
        self.gmrecords = gmrecords
        self._check_arguments()

        event_ids, events = self._get_event_ids_from_args()
        logging.info(f"Number of events to assemble: {len(event_ids)}")

        overwrite = self.gmrecords.args.overwrite
        label = self.gmrecords.args.label

        # label does not get automatically assigned "default" if no input is provided,
        # so it is assigned here
        if label is None:
            label = "default"

        conf = self.gmrecords.conf
        version = self.gmrecords.gmprocess_version
        results = []

        if self.gmrecords.args.num_processes:
            futures = []
            executor = ProcessPoolExecutor(
                max_workers=self.gmrecords.args.num_processes
            )
            for ievent, event_id in enumerate(event_ids):
                logging.info(
                    f"Assembling event {event_id} ({1+ievent} of {len(event_ids)})..."
                )
                event = events[ievent] if events else None
                future = executor.submit(
                    self._assemble_event,
                    event_id,
                    event,
                    self.gmrecords.data_path,
                    overwrite,
                    conf,
                    version,
                    label,
                )
                futures.append(future)
            results = [future.result() for future in futures]
            executor.shutdown()
        else:
            for ievent, event_id in enumerate(event_ids):
                logging.info(
                    f"Assembling event {event_id} ({1+ievent} of {len(event_ids)})..."
                )
                event = events[ievent] if events else None
                results.append(
                    self._assemble_event(
                        event_id,
                        event,
                        self.gmrecords.data_path,
                        overwrite,
                        conf,
                        version,
                        label,
                    )
                )

        for res in results:
            if res is not None:
                self.append_file("Workspace", res)

        self._summarize_files_created()

    # Note: I think that we need to make this a static method in order to be able to
    # call it with ProcessPoolExecutor.
    @staticmethod
    def _assemble_event(event_id, event, data_path, overwrite, conf, version, label):
        event_dir = data_path / event_id
        event_dir.mkdir(exist_ok=True)
        workname = event_dir / constants.WORKSPACE_NAME
        workspace_exists = workname.is_file()
        if workspace_exists:
            logging.info(f"ASDF exists: {str(workname)}")
            if not overwrite:
                logging.info("The --overwrite argument not selected.")
                logging.info(f"No action taken for {event_id}.")
                return None
            else:
                logging.info(f"Removing existing ASDF file: {str(workname)}")
                workname.unlink()
        logging.info(f"Calling assemble function for {event_id}...")
        workspace = assemble_utils.assemble(
            event_id=event_id,
            event=event,
            config=conf,
            directory=data_path,
            gmprocess_version=version,
            label=label,
        )
        logging.info(f"Done with assemble function for {event_id}...")
        if workspace:
            workspace.close()
        return workname
