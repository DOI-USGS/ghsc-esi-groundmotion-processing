"""Module for the processing_stepsModule class."""

import logging
import collections
import inspect

from gmprocess.subcommands.lazy_loader import LazyLoader

base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
STEPS = LazyLoader("steps", globals(), "gmprocess.waveform_processing.processing_step")


class processing_stepsModule(base.SubcommandModule):
    """Print a summary of the currently available processing steps."""

    epilog = """
    These are the processing steps that can be included in the `processing` section of
    the config file.

    The "myst" output type is useful for building docs.
    """

    command_name = "processing_steps"
    aliases = ()

    # Note: do not use the ARG_DICT entry for label because the explanation is
    # different here.
    arguments = [
        {
            "short_flag": "-o",
            "long_flag": "--output-type",
            "help": "File path to save output, formatted as markdown.",
            "default": None,
            "type": str,
            "choices": ["text", "myst"],
        },
        {
            "short_flag": "-p",
            "long_flag": "--path",
            "help": "File path to save output. If unset, then uses standard out.",
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

        if gmrecords.args.path is None:
            for step, func in osteps.items():
                print("")
                print(step)
                print("=" * len(step))
                print(f"{func.__name__}{inspect.signature(func)}\n")
                print(func.__doc__)
        else:
            if gmrecords.args.output_type == "myst":
                with open(gmrecords.args.path, "w") as out:
                    for step, func in osteps.items():
                        out.write("```{eval-rst}\n")
                        func_path = f"{func.__module__}.{func.__name__}"
                        out.write(f".. autofunction:: {func_path}\n")
                        out.write("```\n")
            else:
                with open(gmrecords.args.path, "w") as out:
                    for step, func in osteps.items():
                        out.write("\n")
                        out.write(f"{step}\n")
                        out.write(f"{'=' * len(step)}\n")
                        out.write(f"{func.__name__}{inspect.signature(func)}\n\n")
                        out.write(f"{func.__doc__}\n")
                        out.write("\n")
