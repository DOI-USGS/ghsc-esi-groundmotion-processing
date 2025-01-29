"""Module for SubcommandModule base class."""

import logging
import sys
from abc import ABC, abstractmethod
from pathlib import Path

from gmprocess.subcommands.lazy_loader import LazyLoader

confmod = LazyLoader("confmod", globals(), "gmprocess.utils.config")
ws = LazyLoader("ws", globals(), "gmprocess.io.asdf.stream_workspace")
constants = LazyLoader("constants", globals(), "gmprocess.utils.constants")
scalar_event = LazyLoader("scalar_event", globals(), "gmprocess.core.scalar_event")


class SubcommandModule(ABC):
    """gmprocess base module."""

    @property
    @abstractmethod
    def command_name(self):
        """
        Name of subcommand: string, all lowercase.
        """
        raise NotImplementedError

    """Tuple class variable of subcommand aliases.
    """
    aliases = ()

    def __init__(self):
        """Dictionary instance variable to track files created by module."""
        self.files_created = {}

    def open_workspace(self, event_id):
        """Open workspace, add as attribute."""
        event_dir = Path(self.gmrecords.data_path) / event_id
        workname = event_dir / constants.WORKSPACE_NAME
        if not workname.is_file():
            logging.warning(
                f"No workspace file found for event {event_id}. Please run subcommand "
                "'assemble' to generate workspace file."
            )
            logging.info("Continuing to next event.")
            self.workspace = None
        else:
            self.workspace = ws.StreamWorkspace.open(workname)

    def close_workspace(self):
        """Close workspace."""
        self.workspace.close()

    @property
    @abstractmethod
    def arguments(self):
        """A list of dicts for each argument of the subcommands. Each dict
        should have the following keys: short_flag, long_flag, help, action,
        default.
        """
        raise NotImplementedError

    @abstractmethod
    def main(self, gmrecords):
        """
        All main methods should take one gmp object (a GMrecordsApp instance).
        """
        raise NotImplementedError

    @classmethod
    def list_arguments(cls):
        """List the arguments of the subcommand."""
        arg_list = []
        for arg in cls.arguments:
            arg_list.append(arg["long_flag"].replace("--", "").replace("-", "_"))
        return arg_list

    @classmethod
    def arguments_default_dict(cls):
        """List the arguments of the subcommand."""
        arg_list = cls.list_arguments()
        default_list = [arg["default"] for arg in cls.arguments]
        default_dict = dict(zip(arg_list, default_list))
        return default_dict

    def _check_arguments(self):
        """Check subcommand's arguments are present and fix if not.

        Puts in default value for arguments if argument is not specified.

        Motivation for this is for when the subcommand module is called
        directly, rather than from the gmrecords command line program.
        """
        args = self.gmrecords.args
        req_args = self.arguments_default_dict()
        for arg, val in req_args.items():
            if arg not in args:
                args.__dict__.update({arg: val})

    def _get_event_ids_from_args(self):
        """Get event ids and events from arguments.

        Returns:
            Tuple with event ids (list) and events (ScalarEvent).
        """
        data_path = self.gmrecords.data_path
        user_ids = self.gmrecords.args.event_id
        events_filename = self.gmrecords.args.textfile
        file_ids, events = scalar_event.get_events_from_file(events_filename)
        event_ids = scalar_event.get_event_ids(
            ids=user_ids, file_ids=file_ids, data_dir=data_path
        )

        if self.gmrecords.args.resume:
            if self.gmrecords.args.resume not in event_ids:
                print(
                    f"{self.gmrecords.args.resume} not found in list of event_ids. Exiting."
                )
                sys.exit(1)
            else:
                event_idx = event_ids.index(self.gmrecords.args.resume)
                event_ids = event_ids[event_idx:]
                if events:
                    events = events[event_idx:]

        return (event_ids, events)

    def append_file(self, tag, filename):
        """Convenience method to add file via tag to self.files_created."""
        if tag in self.files_created:
            self.files_created[tag].append(str(filename.resolve()))
        else:
            self.files_created[tag] = [str(filename.resolve())]

    def _summarize_files_created(self):
        if len(self.files_created):
            logging.info("The following files have been created:")
            for file_type, file_list in self.files_created.items():
                logging.info(f"File type: {file_type}")
                for fname in file_list:
                    logging.info(f"\t{fname}")
        else:
            logging.info("No new files created.")

    def _get_pstreams(self, event_id):
        """Convenience method for recycled code."""
        self._get_labels()
        if self.gmrecords.args.label is None:
            return

        config = self._get_config()

        self.pstreams = self.workspace.get_streams(
            event_id, labels=[self.gmrecords.args.label], config=config
        )

    def _get_labels(self):
        labels = self.workspace.get_labels()
        if len(labels) and "unprocessed" in labels:
            labels.remove("unprocessed")
        if not len(labels):
            logging.info(
                f"No processed waveform data in: {self.workspace.dataset.filename}"
            )
            return

        # If there are more than 1 processed labels, prompt user to select
        # one.
        if (len(labels) > 1) and (self.gmrecords.args.label is None):
            print("\nWhich label do you want to use?")
            for lab in labels:
                print(f"\t{lab}")
            tmplab = input("> ")
            if tmplab not in labels:
                print(f"{tmplab} not a valid label. Exiting.")
                sys.exit(1)
            else:
                self.gmrecords.args.label = tmplab
        elif self.gmrecords.args.label is None:
            self.gmrecords.args.label = labels[0]

    def _get_config(self):
        if hasattr(self, "workspace") and hasattr(self.workspace, "config"):
            config = self.workspace.config
        else:
            config = confmod.get_config()
        return config
