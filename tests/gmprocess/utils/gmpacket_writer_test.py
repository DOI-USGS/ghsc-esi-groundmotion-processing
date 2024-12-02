# stdlib imports
import logging
import pathlib
import shutil
import tempfile

# third party imports
import numpy as np
from gmpacket.packet import GroundMotionPacket

# local imports
from gmprocess.utils.export_gmpacket_utils import GroundMotionPacketWriter
from gmprocess.utils.constants import TEST_DATA_DIR


def test_gmpacket_writer(datafile=None, save_file=False):
    if datafile is None:
        datafile = (
            TEST_DATA_DIR / "demo_steps" / "exports" / "ci38457511" / "workspace.h5"
        )

    tempdir = None
    fmt = "%(levelname)s -- %(asctime)s -- %(module)s.%(funcName)s -- %(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt)
    try:
        tempdir = pathlib.Path(tempfile.mkdtemp())
        packet_writer = GroundMotionPacketWriter(tempdir, datafile, label="default")
        files, _, _, _ = packet_writer.write()

        jsonfile = files[0]
        packet = GroundMotionPacket.load_from_json(jsonfile)
        cmp_dict = {
            "id": "ci38457511",
            "time": "2019-07-06T03:19:53.040000",
            "magnitude": 7.1,
            "event_longitude": -117.6,
            "event_latitude": 35.77,
            "event_depth": 8000,
            "network": "CI",
            "station": "CCC",
            "station_name": "China Lake NWC, Christmas Canyon Rd.",
            "station_longitude": -117.36,
            "station_latitude": 35.525,
            "station_elevation": 0.0,
            "epicentral_distance_km": 34.80446348367976,
            "component": "h1",
            "location": "--",
            "PGA(%g)": 48.013,
            "PGV(cm/s)": 78.154,
            "DURATION(s)_Start_percentage_5.0%_End_percentage_75.0%": 8.58,
            "DURATION(s)_Start_percentage_5.0%_End_percentage_95.0%": 11.23,
            "SA(%g)_critical_damping_5.0%_period_0.01s": 48.897,
            "SA(%g)_critical_damping_5.0%_period_0.1s": 86.584,
            "SA(%g)_critical_damping_5.0%_period_0.3s": 102.64,
            "SA(%g)_critical_damping_5.0%_period_1.0s": 72.556,
            "SA(%g)_critical_damping_5.0%_period_3.0s": 19.224,
            "SA(%g)_critical_damping_5.0%_period_10.0s": 1.2782,
        }
        df = packet.to_dataframe()
        for key, newvalue in df.iloc[0].to_dict().items():
            cmpvalue = cmp_dict[key]
            if isinstance(newvalue, str):
                assert newvalue == cmpvalue
            else:
                np.testing.assert_allclose(newvalue, cmpvalue)
        if save_file:
            for file in files:
                outfile = pathlib.Path.home() / file.name
                print(f"Saving file {outfile}...")
                shutil.copy(file, outfile)
        del packet_writer
    finally:
        if tempdir is not None:
            shutil.rmtree(tempdir)
