#!/usr/bin/env python

# stdlib imports
import logging
import pathlib
import shutil
import sys
import tempfile

# third party imports
from gmpacket.packet import GroundMotionPacket

# local imports
from gmprocess.utils.export_gmpacket_utils import GroundMotionPacketWriter


def test_gmpacket_writer(datafile=None, save_file=False):
    if datafile is None:
        datafile = (
            pathlib.Path(__file__).parent
            / ".."
            / ".."
            / ".."
            / "src"
            / "gmprocess"
            / "data"
            / "asdf"
            / "nc72282711"
            / "workspace.h5"
        )
    tempdir = None
    fmt = "%(levelname)s -- %(asctime)s -- %(module)s.%(funcName)s -- %(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt)
    try:
        tempdir = pathlib.Path(tempfile.mkdtemp())
        packet_writer = GroundMotionPacketWriter(tempdir, datafile, label="default")
        files, nevents, nstreams, ntraces = packet_writer.write()

        jsonfile = files[0]
        packet = GroundMotionPacket.load_from_json(jsonfile)

        cmp_dict = {
            "id": "nc72282711",
            "time": "2014-08-24T10:20:44Z",
            "magnitude": 6.02,
            "event_longitude": -122.31,
            "event_latitude": 38.215,
            "event_depth": 11120,
            "network": "NP",
            "station": "1743",
            "station_name": "CA:Petaluma;FS 2",
            "station_longitude": -122.66,
            "station_latitude": 38.267,
            "station_elevation": 9.0,
            "component": "H1",
            "location": "",
            "PGA(cm/s^2)": 3.4837,
            "PGV(cm/s)": 5.898,
            "SORTED_DURATION(s)": 11.77,
            "DURATION(s)_Start_percentage_5.0%_End_percentage_75.0%": 13.43,
            "DURATION(s)_Start_percentage_5.0%_End_percentage_95.0%": 25.195,
            "SA(g)_critical_damping_5.0%_period_0.01s": 3.5175,
            "SA(g)_critical_damping_5.0%_period_0.02s": 3.4998,
            "SA(g)_critical_damping_5.0%_period_0.03s": 3.5191,
            "SA(g)_critical_damping_5.0%_period_0.05s": 3.7155,
            "SA(g)_critical_damping_5.0%_period_0.075s": 4.8891,
            "SA(g)_critical_damping_5.0%_period_0.1s": 4.9017,
            "SA(g)_critical_damping_5.0%_period_0.15s": 9.3838,
            "SA(g)_critical_damping_5.0%_period_0.2s": 11.279,
            "SA(g)_critical_damping_5.0%_period_0.25s": 12.191,
            "SA(g)_critical_damping_5.0%_period_0.3s": 8.8725,
            "SA(g)_critical_damping_5.0%_period_0.4s": 10.716,
            "SA(g)_critical_damping_5.0%_period_0.5s": 8.7577,
            "SA(g)_critical_damping_5.0%_period_0.75s": 6.146,
            "SA(g)_critical_damping_5.0%_period_1.0s": 4.9289,
            "SA(g)_critical_damping_5.0%_period_1.5s": 4.0151,
            "SA(g)_critical_damping_5.0%_period_10.0s": 0.13805,
            "SA(g)_critical_damping_5.0%_period_2.0s": 4.1278,
            "SA(g)_critical_damping_5.0%_period_3.0s": 4.4347,
            "SA(g)_critical_damping_5.0%_period_4.0s": 1.3209,
            "SA(g)_critical_damping_5.0%_period_5.0s": 0.60831,
            "SA(g)_critical_damping_5.0%_period_7.5s": 0.26031,
        }
        df = packet.to_dataframe()
        assert df.iloc[0].to_dict() == cmp_dict
        if save_file:
            for file in files:
                outfile = pathlib.Path.home() / file.name
                print(f"Saving file {outfile}...")
                shutil.copy(file, outfile)
        del packet_writer
    finally:
        if tempfile is not None:
            shutil.rmtree(tempdir)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_gmpacket_writer(sys.argv[1], save_file=bool(sys.argv[2]))
    else:
        test_gmpacket_writer()
