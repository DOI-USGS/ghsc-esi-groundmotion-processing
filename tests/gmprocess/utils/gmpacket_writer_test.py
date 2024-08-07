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
        # datafile = DATA_DIR / "asdf" / "nc72282711" / "workspace.h5"
        datafile = (
            TEST_DATA_DIR
            / "demo_steps"
            / "exports"
            / "ci38457511"
            / "workspace.h5"
        )

    tempdir = None
    fmt = (
        "%(levelname)s -- %(asctime)s -- %(module)s.%(funcName)s -- %(message)s"
    )
    logging.basicConfig(level=logging.INFO, format=fmt)
    try:
        tempdir = pathlib.Path(tempfile.mkdtemp())
        packet_writer = GroundMotionPacketWriter(
            tempdir, datafile, label="default"
        )
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
            "PGA(%g)": 47.018,
            "PGV(cm/s)": 78.085,
            "SortedDuration(s)": 5.89,
            "DURATION(s)_Start_percentage_5.0%_End_percentage_75.0%": 8.61,
            "DURATION(s)_Start_percentage_5.0%_End_percentage_95.0%": 11.28,
            "SA(%g)_critical_damping_5.0%_period_0.01s": 47.779,
            "SA(%g)_critical_damping_5.0%_period_0.02s": 48.454,
            "SA(%g)_critical_damping_5.0%_period_0.03s": 52.475,
            "SA(%g)_critical_damping_5.0%_period_0.05s": 84.145,
            "SA(%g)_critical_damping_5.0%_period_0.075s": 109.44,
            "SA(%g)_critical_damping_5.0%_period_0.1s": 87.504,
            "SA(%g)_critical_damping_5.0%_period_0.15s": 111.85,
            "SA(%g)_critical_damping_5.0%_period_0.2s": 102.9,
            "SA(%g)_critical_damping_5.0%_period_0.25s": 89.782,
            "SA(%g)_critical_damping_5.0%_period_0.3s": 102.78,
            "SA(%g)_critical_damping_5.0%_period_0.4s": 136.33,
            "SA(%g)_critical_damping_5.0%_period_0.5s": 114.33,
            "SA(%g)_critical_damping_5.0%_period_0.75s": 87.7,
            "SA(%g)_critical_damping_5.0%_period_1.0s": 72.637,
            "SA(%g)_critical_damping_5.0%_period_1.5s": 53.539,
            "SA(%g)_critical_damping_5.0%_period_10.0s": 1.4379,
            "SA(%g)_critical_damping_5.0%_period_2.0s": 25.128,
            "SA(%g)_critical_damping_5.0%_period_3.0s": 19.283,
            "SA(%g)_critical_damping_5.0%_period_4.0s": 15.595,
            "SA(%g)_critical_damping_5.0%_period_5.0s": 11.987,
            "SA(%g)_critical_damping_5.0%_period_7.5s": 2.8246,
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
