#!/usr/bin/env python

import argparse
import h5py
import numpy as np
from pathlib import Path

import pyasdf
from pyasdf.inventory_utils import isolate_and_merge_station


def main():
    description = """This script fixes how some station metadata is stored in the 
    workspace file. The problem is that we were storing supplemental data in the 
    StationXML file by abusing the "description" field. This script will move the info 
    from this location to auxiliary data."""
    parser = argparse.ArgumentParser(description=description)
    path_group = parser.add_mutually_exclusive_group()
    path_group.add_argument(
        "--project-data-path",
        help="Path to a gmprocess project data directory.",
        type=str,
    )
    path_group.add_argument(
        "--event-dir-path",
        help="Path to a gmprocess event directory.",
        type=str,
    )
    path_group.add_argument(
        "--file",
        help="Path to a gmprocess workspace file.",
        type=str,
    )
    args = parser.parse_args()
    file_list = _get_file_list(args)
    FixInventory(file_list)


class FixInventory:
    """Class to fix gmprocess inventories."""

    def __init__(self, file_list):
        """
        Args:
            file_list (list):
                List of files to fix.
        """
        self.file_list = file_list
        for self.file in self.file_list:
            if not self.file.exists():
                raise ValueError(f"File {self.file} does not exist.")
            print(f"Fixing file {self.file}")
            self.fix_inventory()

    def fix_inventory(self):
        """Fix inventory in workspace file.

        Args:
            filename (str):
                Path to workspace file.
        """
        self.get_all_inventories()
        self.move_description_to_aux()
        self.fix_inventories()
        self.delete_stationxml()
        self.add_fixed_stationxml()

    def get_all_inventories(self):
        ds = pyasdf.ASDFDataSet(self.file)
        self.inventories = []
        for waveform in ds.waveforms:
            if "StationXML" not in waveform:
                self.inventories.append("")
            self.inventories.append(waveform.StationXML)
        del ds

    def move_description_to_aux(self):
        # move description to aux data
        aux_group_name = "StreamSupplementalStats"
        ds = pyasdf.ASDFDataSet(self.file)
        for i, waveform in enumerate(ds.waveforms):
            tags = waveform.get_waveform_tags()
            for tag in tags:
                stream = waveform[tag]
                stats = stream[0].stats
                for net in self.inventories[i]:
                    for station in net.stations:
                        net_sta = f"{net.code}.{station.code}"
                        station_label = (
                            f"{net_sta}.{stats.location}.{stats.channel[0:2]}_{tag}"
                        )
                        # does this data already exist?
                        if aux_group_name in ds.auxiliary_data:
                            if net_sta in ds.auxiliary_data[aux_group_name]:
                                if (
                                    station_label
                                    in ds.auxiliary_data[aux_group_name][net_sta]
                                ):
                                    continue
                        databuf = station.description.encode("utf-8")
                        data_array = np.frombuffer(databuf, dtype=np.uint8)
                        stream_path = f"{net_sta}/{station_label}"
                        ds.add_auxiliary_data(
                            data_array,
                            data_type=aux_group_name,
                            path=stream_path,
                            parameters={},
                        )
        del ds

    def fix_inventories(self):
        ds = pyasdf.ASDFDataSet(self.file)
        for i, waveform in enumerate(ds.waveforms):
            tags = waveform.get_waveform_tags()
            for _ in tags:
                for net in self.inventories[i]:
                    for sta in net.stations:
                        sta.description = ""
        del ds

    def delete_stationxml(self):
        h5 = h5py.File(self.file, "r+")
        for sta in h5["Waveforms"]:
            if "StationXML" in sta:
                del sta["StationXML"]
        h5.flush()
        h5.close()

    def add_fixed_stationxml(self):
        ds = pyasdf.ASDFDataSet(self.file)
        for i, _ in enumerate(ds.waveforms):
            for net in self.inventories[i]:
                for station in net.stations:
                    ds._add_inventory_object(
                        isolate_and_merge_station(
                            self.inventories[i],
                            network_id=net.code,
                            station_id=station.code,
                        ),
                        net.code,
                        station.code,
                    )
        del ds


def _get_file_list(args):
    if args.file:
        return [Path(args.file)]
    elif args.event_dir_path:
        return [Path(args.event_dir_path).expanduser() / "workspace.h5"]
    elif args.project_data_path:
        event_dirs = Path(args.project_data_path).expanduser().glob("*/")
        return [d / "workspace.h5" for d in event_dirs]


if __name__ == "__main__":
    main()
