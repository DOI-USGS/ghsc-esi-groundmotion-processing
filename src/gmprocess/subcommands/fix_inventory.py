#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import numpy as np
import h5py

import pyasdf
from pyasdf.inventory_utils import isolate_and_merge_station

from gmprocess.subcommands.lazy_loader import LazyLoader

base = LazyLoader("base", globals(), "gmprocess.subcommands.base")


class FixInventoryModule(base.SubcommandModule):
    """Fix inventory in workspace file.

    The problem is that we were storing supplemental data in the StationXML file by
    abusing the "description" field. This script will move the info from this location
    to auxiliary data.
    """

    command_name = "fix_inventory"

    arguments = []

    def main(self, gmrecords):
        """
        Fix inventory in workspace file.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info(f"Running subcommand '{self.command_name}'")
        self.gmrecords = gmrecords
        self._get_events()
        self._check_arguments()

        logging.info(f"Number of events: {len(self.events)}")
        for event in self.events:
            event_dir = gmrecords.data_path / event.id
            workspace_file = event_dir / "workspace.h5"
            fix_inventory(workspace_file)


def fix_inventory(filename):
    """Fix inventory in workspace file.

    Args:
        filename (str):
            Path to workspace file.
    """

    # get all inventories
    ds = pyasdf.ASDFDataSet(filename)
    inventories = []
    for waveform in ds.waveforms:
        if "StationXML" not in waveform:
            inventories.append("")
        inventories.append(waveform.StationXML)
    del ds
    logging.info(f"Found {len(inventories)} inventories.")

    # move description to aux data
    aux_group_name = "StreamSupplementalStats"
    ds = pyasdf.ASDFDataSet(filename)
    logging.info("Moving description to aux...")
    for i, waveform in enumerate(ds.waveforms):
        logging.info(f"Moving description to aux for {ds.waveforms}")
        tags = waveform.get_waveform_tags()
        for tag in tags:
            logging.info(f"  Tag: {tag}")
            stream = waveform[tag]
            stats = stream[0].stats
            for net in inventories[i]:
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
                                logging.info(
                                    f"  {aux_group_name} already exists, skipping."
                                )
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
                    logging.info(f"  added {aux_group_name} to {stream_path}")
    del ds

    # fix inventories
    logging.info("Fixing description...")
    ds = pyasdf.ASDFDataSet(filename)
    for i, waveform in enumerate(ds.waveforms):
        logging.info(f"Fixing description for {ds.waveforms}")
        tags = waveform.get_waveform_tags()
        for tag in tags:
            logging.info(f"  Tag: {tag}")
            stream = waveform[tag]
            stats = stream[0].stats
            for net in inventories[i]:
                for sta in net.stations:
                    sta.description = ""
    del ds

    # delete stationxml from h5 file with h5py
    logging.info("Removing bad inventories...")
    h5 = h5py.File(filename, "r+")
    for sta in h5["Waveforms"]:
        if "StationXML" in sta:
            del sta["StationXML"]
    h5.flush()
    h5.close()

    # add fixed stationxml to workspace
    logging.info("Adding fixed inventories...")
    ds = pyasdf.ASDFDataSet(filename)
    for i, waveform in enumerate(ds.waveforms):
        logging.info(f"Adding inventory for {ds.waveforms}")
        for net in inventories[i]:
            for station in net.stations:
                net_sta = f"{net.code}.{station.code}"
                ds._add_inventory_object(
                    isolate_and_merge_station(
                        inventories[i],
                        network_id=net.code,
                        station_id=station.code,
                    ),
                    net.code,
                    station.code,
                )
    del ds
