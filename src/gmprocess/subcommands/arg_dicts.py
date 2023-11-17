"""Module for shared subcommand arguments."""

ARG_DICTS = {
    "output_format": {
        "short_flag": "-f",
        "long_flag": "--output-format",
        "help": "Output file format.",
        "type": str,
        "default": "csv",
        "choices": ["excel", "csv"],
    },
}
