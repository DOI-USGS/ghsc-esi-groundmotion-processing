#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import collections

from gmprocess.subcommands.lazy_loader import LazyLoader

base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
STEPS = LazyLoader("steps", globals(), "gmprocess.waveform_processing.processing_step")


class ProcessWaveformsModule(base.SubcommandModule):
    """Print a summary of the currently available processing steps."""

    epilog = """
    These are the processing steps that can be included in the `processing` section of
    the config file.
    """

    command_name = "processing_steps"
    aliases = ()

    # Note: do not use the ARG_DICT entry for label because the explanation is
    # different here.
    arguments = []

    def main(self, gmrecords):
        """Summarize available processing steps and their arguments.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info(f"Running subcommand '{self.command_name}'")

        steps = STEPS.collect_processing_steps()
        osteps = collections.OrderedDict(
            sorted(steps.items(), key=lambda tup: tup[0].lower())
        )

        print("")
        for step, func in osteps.items():
            print(step)
            print("=" * len(step))
            print(func.__doc__)
            print("")
