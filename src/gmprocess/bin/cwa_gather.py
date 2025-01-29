#!/usr/bin/env python

# stdlib imports
import os
import argparse
import sys
import pathlib

# third party imports
import numpy as np
from obspy import read, read_inventory
import configobj

# local imports
from gmprocess.core import scalar_event
from gmprocess.utils import constants
from gmprocess.utils import download_utils
from gmprocess.core.scalar_event import ScalarEvent


class App:
    """App to facilitate getting CWA data into gmprocess."""

    @staticmethod
    def main(event_id, datafile, metadata):
        """Application driver method.

        Args:
            event_id (str):
                Event id.
            datafile (str):
                The <eventid>_*_data.mseed file that you downloaded.
            metadata (str):
                StationXML file that you downloaded.
        """

        if "CALLED_FROM_PYTEST" in os.environ:
            CONF_PATH = pathlib.Path(".") / ".gmprocess"
        else:
            CONF_PATH = pathlib.Path.home() / ".gmprocess"
        PROJECTS_FILE = CONF_PATH / "projects.conf"
        projects_conf = configobj.ConfigObj(str(PROJECTS_FILE), encoding="utf-8")
        project = projects_conf["project"]
        current_project = projects_conf["projects"][project]
        data_parts = pathlib.PurePath(current_project["data_path"]).parts
        data_path = CONF_PATH.joinpath(*data_parts).resolve()
        event_path = data_path / event_id
        raw_path = event_path / "raw"
        if not event_path.exists():
            event_path.mkdir()
            raw_path.mkdir()
        raw_stream = read(datafile)
        # some of these files are returned from CWB web site in time chunks
        # using this merge method joins up all of the traces with the same
        # NSCL. Thanks Obspy!
        stream = raw_stream.merge()
        trace_count = 0
        for trace in stream:
            if isinstance(trace.data, np.ma.core.MaskedArray):
                continue
            network = trace.stats.network
            station = trace.stats.station
            channel = trace.stats.channel
            location = trace.stats.location
            starttime_str = trace.stats.starttime.strftime("%Y%m%dT%H%M%SZ")
            endtime_str = trace.stats.endtime.strftime("%Y%m%dT%H%M%SZ")
            fname = (
                f"{network}.{station}.{location}.{channel}__"
                f"{starttime_str}__{endtime_str}.mseed"
            )
            filename = raw_path / fname
            trace.write(str(filename), format="MSEED")
            trace_count += 1
        print(f"{len(stream)} channels written to {raw_path}.")

        inventory = read_inventory(metadata)
        network = inventory.networks[0]
        netcode = network.code
        for station in network.stations:
            stacode = station.code
            xml_name = f"{netcode}.{stacode}.xml"
            sta_inv = inventory.select(netcode, stacode)
            # Correct HL channel codes to be HN
            for net in sta_inv.networks:
                for sta in net.stations:
                    for chan in sta.channels:
                        if chan.code.startswith("HL"):
                            chan.code = chan.code[0] + "N" + chan.code[2]
            sta_inv.write(raw_path / xml_name, "STATIONXML")
        print(f"{len(network.stations)} StationXML files written to {raw_path}.")

        event_info = download_utils.download_comcat_event(event_id)
        scalar_event.write_geojson(event_info, event_path)
        event_file = event_path / constants.EVENT_FILE
        msg = f"Created event file at {event_file}."
        if not event_file.is_file():
            msg = f"Error: Failed to create {event_file}."
        print(msg)
        download_utils.download_rupture_file(event_id, event_path)
        rupture_file = event_path / "rupture.json"
        msg = f"Created rupture file at {rupture_file}."
        if not rupture_file.is_file():
            msg = f"Warning: Failed to create {rupture_file}."
        print(msg)

        event = ScalarEvent.from_json(event_file)
        download_utils.get_strec_results(event, event_path)
        msg = "Downloaded STREC results."
        strec_file = event_path / "strec_results.json"
        if not strec_file.is_file():
            msg = "Failed to download STREC results."
        print(msg)


def cli():
    """Command line interface to the cwa_gather application."""

    desc = """Convert CWA data from web site into form ingestible by gmprocess.

    To obtain CWA strong motion data, create an account on the CWA:

    https://gdms.cwa.gov.tw/


    Step 1: CWBSN metadata
    ----------------------

    Click on the "Data" icon, then click on "Instrument Response". 

     - For "Output Format", choose "Station XML".
     - For "Network", choose "CWBSN".
     - For "Station", check "All Stations".
     - For "Location", choose "*" for all locations.
     - For "Channel", choose "HN?" for all strong motion stations.
     - For "Start Time (UTC)", enter a date before the event of interest.
     - For "End Time (UTC)", enter a date after the event of interest.
     - "Label", doesn't matter because they don't use what you put here.
     - Click the "Submit" button, and you should see a "Success!" pop up.
     - Next will be a screen showing a list of all of your downloads.
     - Right click on the most recent entry, it will be called "output.stationXML"
     - Select "save link as" and name it <eventid>_cwbsn.xml
     
    Step 2: TSMIP metadata
    ----------------------

    Click on the "Data" icon, then click on "Instrument Response". 

     - For "Output Format", choose "Station XML".
     - For "Network", choose "TSMIP".
     - For "Station", check "All Stations".
     - For "Location", choose "*" for all locations.
     - For "Channel", choose "HL?" for all strong motion stations.
     - For "Start Time (UTC)", enter a date before the event of interest.
     - For "End Time (UTC)", enter a date after the event of interest.
     - "Label", doesn't matter becasue they don't use what you put here.
     - Click the "Submit" button, and you should see a "Success!" pop up.
     - Next will be a screen showing a list of all of your downloads.
     - Right click on the most recent entry, it will be called "output.stationXML"
     - Select "save link as" and name it <eventid>_tsmip.xml

    Step 3: CWBSN ground motions
    ----------------------------

    Click on the "Data" icon, then click on "Multi-Station Waveform Data". 

     - For "Output Format", choose "MiniSEED".
     - For "Network", choose "CWBSN".
     - For "Station", check "All Stations".
     - For "Location", choose "*" for all locations.
     - For "Channel", choose "HN?" for all strong motion stations.
     - For "Start Time (UTC)", enter a time 30 seconds before the origin time of 
       interest.
     - For "End Time (UTC)", enter a time 4 minutes after the origin time of interest.
       Note that this can be adjusted up for larger earthquakes or down for smaller.
     - For "Label" use <eventid>_cwbsn_data
     - Click the "Submit" button, and you should see a "Success!" pop up.
     - Next will be a screen showing a list of all of your downloads. Data links will
       take a few minutes to process.
     - Download the file, which will be named <eventid>_cwbsn_data

    Step 4: TSMIP ground motions
    ----------------------------

    Click on the "Data" icon, then click on "Multi-Station Waveform Data". 

     - For "Output Format", choose "MiniSEED".
     - For "Network", choose "TSMIP".
     - For "Station", check "All Stations".
     - For "Location", choose "*" for all locations.
     - For "Channel", choose "HN?" for all strong motion stations.
     - For "Start Time (UTC)", enter a time 30 seconds before the origin time of 
       interest.
     - For "End Time (UTC)", enter a time 4 minutes after the origin time of interest.
       Note that this can be adjusted up for larger earthquakes or down for smaller.
     - For "Label" use <eventid>_tsmip_data
     - Click the "Submit" button, and you should see a "Success!" pop up.
     - Next will be a screen showing a list of all of your downloads. Data links will
       take a few minutes to process.
     - Download the file, which will be named <eventid>_tsmip_data
     

    You will need to run the cwa_gather command twice, once for each pair of XML and
    tgz files for the CWBSN and TSMIP networks.
    """

    parser = argparse.ArgumentParser(
        description=desc,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--event",
        dest="event_id",
        help="ComCat Event ID",
    )
    parser.add_argument(
        "datafile",
        help="The <eventid>_*_data.mseed file that you downloaded.",
    )
    parser.add_argument(
        "metadata",
        help="StationXML file that you downloaded.",
    )
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    app = App()
    app.main(args.event_id, args.datafile, args.metadata)


if __name__ == "__main__":
    cli()
