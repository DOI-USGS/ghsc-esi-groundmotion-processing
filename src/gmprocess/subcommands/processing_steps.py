#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import collections

from gmprocess.subcommands.lazy_loader import LazyLoader

base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
STEPS = LazyLoader("steps", globals(), "gmprocess.waveform_processing.processing_step")


class ProcessingStepsModule(base.SubcommandModule):
    """Print a summary of the currently available processing steps."""

    epilog = """
    These are the processing steps that can be included in the `processing` section of
    the config file.
    """

    command_name = "processing_steps"
    aliases = ()

    # Note: do not use the ARG_DICT entry for label because the explanation is
    # different here.
    arguments = [
        {
            "short_flag": "-o",
            "long_flag": "--output-markdown",
            "help": ("File path to save output, formated as markdown."),
            "default": None,
            "type": str,
        },
    ]

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

        if gmrecords.args.output_markdown is None:
            for step, func in osteps.items():
                print("")
                print(step)
                print("=" * len(step))
                print(func.__doc__)
        else:
            with open(gmrecords.args.output_markdown, "w") as out:
                for step, func in osteps.items():
                    out.write("\n")
                    out.write("## " + step + "\n")
                    out.write("```\n")
                    out.write(func.__doc__ + "\n")
                    out.write("```\n")
