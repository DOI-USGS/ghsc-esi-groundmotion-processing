#!/usr/bin/env python

import argparse
from pathlib import Path

from ruamel.yaml import YAML

from gmprocess.io.asdf.stream_workspace import StreamWorkspace


def save_config(ws, out_file):
    group_name = "config/config"
    config_exists = group_name in ws.dataset._auxiliary_data_group
    if config_exists:
        fname = Path(out_file)
        yaml = YAML()
        yaml.indent(mapping=4)
        yaml.preserve_quotes = True
        with open(fname, "a", encoding="utf-8") as yf:
            yaml.dump(ws.config, yf)
        print("gmprocess_config:")
        print(f"  Input file: {ws.filename}")
        print(f"  Output file: {fname}")
    else:
        print("No config in workspace.")


def update_config(ws, in_file):
    in_config_path = Path(in_file)
    with open(in_config_path, "r", encoding="utf-8") as f:
        yaml = YAML()
        yaml.preserve_quotes = True
        in_config = yaml.load(f)

    ws.add_config(config=in_config, force=True)
    print("gmprocess_config:")
    print(f"  Input file: {in_file}")
    print(f"  Updated config: {ws.filename}")


def main():
    parser = argparse.ArgumentParser(
        description="""Help to update and review configs in the workspace files.
        
There are two main uses for this command:
- Update the config content that is in a workspace file (use the `--infile` flag).
- Save the config that is in a workspace file to an external text file (use the 
  `--outfile` flag).
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--workspace",
        required=True,
        help="Path to workspace file.",
        type=str,
    )
    io_group = parser.add_mutually_exclusive_group(required=True)
    io_group.add_argument(
        "--outfile",
        help="File to save the contents of the workspace config file to.",
        type=str,
    )
    io_group.add_argument(
        "--infile",
        help="Path to a config file to overwrite the config in the workspace file.",
        type=str,
    )
    args = parser.parse_args()
    ws = StreamWorkspace.open(args.workspace)
    if args.outfile is not None:
        save_config(ws, args.outfile)
    if args.infile is not None:
        update_config(ws, args.infile)
    ws.close()


if __name__ == "__main__":
    main()
