# stdlib imports
import pathlib
import tempfile
import time
from io import StringIO

# local imports
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.io.cosmos.core import is_cosmos, read_cosmos
from gmprocess.io.cosmos.cosmos_writer import (
    CosmosWriter,
    DataBlock,
    FloatHeader,
    IntHeader,
    TextHeader,
    Volume,
)

# third party imports
from obspy.core.utcdatetime import UTCDateTime

SAMPLE_INT_HDR = """
 100 Integer-header values follow on  10 lines, Format= (10I8)
       2       1       4     120       1    -999    -999    -999    -999    -999
       5       5    -999    -999    -999    -999    -999    -999     999    -999
    -999    -999       3    -999    -999    -999    -999    -999    -999    -999
       3    -999    -999    -999    -999    -999    -999    -999    -999    2021
     354      12      20      20      13       5    -999    -999    -999       1
    -999    -999    -999     270    -999    -999    -999    -999    -999       5
    -999       5    -999       1    -999    -999    -999    -999    -999    -999
    -999    -999    -999    -999       1       0    -999    -999    -999    -999
    -999    -999    -999    -999    -999    -999    -999    -999    -999    -999
    -999    -999    -999    -999    -999    -999    -999    -999    -999    -999
"""

SAMPLE_FLOAT_HDR = """
 100 Real-header values follow on 20 lines , Format = (5F15.6)
      39.923300    -123.761400     245.000000    -999.000000    -999.000000
    -999.000000    -999.000000    -999.000000    -999.000000      40.349833
    -124.899333      19.880000       4.840000    -999.000000    -999.000000
    -999.000000     107.924360     115.661748    -999.000000    -999.000000
    -999.000000    -999.000000    -999.000000       1.998079     118.901921
    -999.000000    -999.000000    -999.000000    -999.000000      55.850000
       0.000000       0.000000    -999.000000       0.010000     120.910000
    -999.000000    -999.000000    -999.000000    -999.000000    -999.000000
    -999.000000    -999.000000    -999.000000    -999.000000    -999.000000
    -999.000000    -999.000000    -999.000000    -999.000000    -999.000000
    -999.000000    -999.000000    -999.000000      12.940812    -999.000000
    -999.000000       0.656950    -999.000000    -999.000000    -999.000000
    -999.000000      10.000000     120.910000       0.587939      17.080000
      -0.000000    -999.000000    -999.000000    -999.000000    -999.000000
    -999.000000    -999.000000    -999.000000    -999.000000    -999.000000
    -999.000000    -999.000000    -999.000000    -999.000000    -999.000000
    -999.000000    -999.000000    -999.000000    -999.000000    -999.000000
    -999.000000    -999.000000    -999.000000    -999.000000    -999.000000
    -999.000000    -999.000000    -999.000000    -999.000000    -999.000000
    -999.000000    -999.000000    -999.000000    -999.000000    -999.000000
"""

SAMPLE_RAW_TEXT_HEADER = """
Raw acceleration counts   (Format v01.20 with 13 text lines) ASDF Converted
Record of nc71126864      Earthquake of Mon Dec 20, 2021 20:13 UTC
Hypocenter: 40.350   -124.899   H= 20km(NCSN) M=4.8
Origin: 12/20/2021, 20:13:40.7 UTC (NCSN)
Statn No: 05-    0  Code:CE-79435  CGS  Leggett - Confusion Hill Bridge Grnds
Coords: 39.9233 -123.7614  Site geology:Unknown
Recorder:        s/n:     (  3 Chns of  3 at Sta) Sensor:Kinemetr   s/n
Rcrd start time:12/20/2021, 20:13:10.750 UTC (Q= ) RcrdId:(see comment)
Sta Chan   1:270 deg (Rcrdr Chan  1) Location:10
Raw record length = 450.000 sec, Uncor max =12703.000 counts at   62.180 sec
Processed:                               Max = 12703.000 counts   at  62.180 sec
Record filtered below  Hz      (periods over  secs)       and above  Hz
Values used when parameter or data value is unknown/unspecified:   -999, -999.0
"""

SAMPLE_PROCESSED_TEXT_HDR = """
Corrected acceleration    (Format v01.20 with 13 text lines) ASDF Converted
Record of nc71126864      Earthquake of Mon Dec 20, 2021 20:13 UTC
Hypocenter: 40.350   -124.899   H= 20km(NCSN) M=4.8
Origin: 12/20/2021, 20:13:40.7 UTC (NCSN)
Statn No: 05-    0  Code:CE-79435  CGS  Leggett - Confusion Hill Bridge Grnds
Coords: 39.9233 -123.7614  Site geology:Unknown
Recorder:        s/n:     (  3 Chns of  3 at Sta) Sensor:Kinemetr   s/n
Rcrd start time:12/20/2021, 20:13:55.850 UTC (Q= ) RcrdId:(see comment)
Sta Chan   1:270 deg (Rcrdr Chan  1) Location:10
Raw record length = 120.910 sec, Uncor max =    0.000        at    0.000 sec
Processed:                               Max =     0.588 cm/s^2   at  17.080 sec
Record filtered below  0.66 Hz (periods over   1.5 secs)  and above 12.9 Hz
Values used when parameter or data value is unknown/unspecified:   -999, -999.0
"""

SAMPLE_DATA_BLOCK = """
   6 Comment line(s) follow, each starting with a "|":
| Sensor: Kinemetrics_Episensor
| RcrdId: NC.71126864.CE.79435.HNE.10
|<SCNL>79435.HNE.CE.10 <AUTH> 2024/06/03 20:04:02.480962
|<PROCESS>Automatically processed using gmprocess version 1.1.11
|<eventURL>For updated information about the earthquake visit the URL below:
|<eventURL>https://earthquake.usgs.gov/earthquakes/eventpage/nc71126864
   12091 acceleration pts, approx  120 secs, units=cm/s^2 (4),Format=(1F15.6E)
  -2.770328E-05
  -3.681258E-05
  -4.259866E-05
  -4.462146E-05
  -4.379579E-05
  -4.164551E-05
  -3.943235E-05
  -3.769327E-05
  -3.635931E-05
  -3.521712E-05
  -3.427634E-05
  -3.373357E-05
  -3.358734E-05
  -3.330256E-05
  -3.196328E-05
  -2.898947E-05
  -2.493209E-05
  -2.155079E-05
  -2.074037E-05
  -2.286518E-05
  -2.592247E-05
  -2.667892E-05
  -2.332712E-05
  -1.751760E-05
  -1.360132E-05
  -1.508348E-05
  -2.100227E-05
  -2.562459E-05
"""

INT_SAMPLE_DATA_BLOCK = """
   6 Comment line(s) follow, each starting with a "|":
| Sensor: Kinemetrics_Episensor
| RcrdId: NC.71126864.CE.79435.HNE.10
|<SCNL>79435.HNE.CE.10 <AUTH> 2024/06/03 20:07:55.027759
|<PROCESS>Created using gmprocess version 1.1.11
|<eventURL>For updated information about the earthquake visit the URL below:
|<eventURL>https://earthquake.usgs.gov/earthquakes/eventpage/nc71126864
   45000 acceleration pts, approx  449 secs, units=counts (50),Format=(1I8)
  -11547
  -11307
  -11515
  -11419
  -11404
  -11576
  -11343
  -11397
  -11540
  -11411
  -11405
  -11408
"""

TEST_DATA_DIR = (pathlib.Path(__file__).parent / ".." / ".." / "..").resolve()


def get_sample_data(volume):
    datafile = TEST_DATA_DIR / "data" / "asdf" / "nc71126864" / "workspace.h5"
    workspace = StreamWorkspace.open(datafile)
    t1 = time.time()
    eventid = workspace.get_event_ids()[0]
    t2 = time.time()
    print(f"{t2-t1:.2f} seconds to read eventid")
    scalar_event = workspace.get_event(eventid)

    station = "CE.79435"
    labels = workspace.get_labels()
    if volume == Volume.RAW:
        labels.remove("default")
    elif volume == Volume.CONVERTED:
        labels.remove("default")
    else:
        labels.remove("unprocessed")
    plabel = labels[0]
    streams = workspace.get_streams(eventid, stations=[station], labels=[plabel])
    gmprocess_version = workspace.get_gmprocess_version()
    idx = gmprocess_version.find(".dev")
    gmprocess_version = gmprocess_version[0:idx]
    stream = streams[0]
    trace = stream[0]
    workspace.close()
    return (trace, eventid, scalar_event, stream, gmprocess_version)


def test_text_header():
    # get some data
    volume = Volume.PROCESSED
    trace, _, scalar_event, stream, gmprocess_version = get_sample_data(volume)
    text_header = TextHeader(trace, scalar_event, stream, volume, gmprocess_version)
    cosmos_file = StringIO()
    text_header.write(cosmos_file)
    output = cosmos_file.getvalue()
    sample_lines = SAMPLE_PROCESSED_TEXT_HDR.lstrip().split("\n")
    for idx, line1 in enumerate(output.split("\n")):
        line2 = sample_lines[idx]
        assert line1.strip() == line2.strip()

    # get some data
    volume = Volume.RAW
    trace, _, scalar_event, stream, gmprocess_version = get_sample_data(volume)
    text_header = TextHeader(trace, scalar_event, stream, volume, gmprocess_version)
    cosmos_file = StringIO()
    text_header.write(cosmos_file)
    output = cosmos_file.getvalue()
    sample_lines = SAMPLE_RAW_TEXT_HEADER.lstrip().split("\n")
    for idx, line1 in enumerate(output.split("\n")):
        line2 = sample_lines[idx]
        assert line1.strip() == line2.strip()


def test_int_header():
    volume = Volume.PROCESSED
    trace, _, scalar_event, stream, gmprocess_version = get_sample_data(volume)
    int_header = IntHeader(trace, scalar_event, stream, volume, gmprocess_version)
    cosmos_file = StringIO()
    int_header.write(cosmos_file)
    output = cosmos_file.getvalue()
    sample_lines = SAMPLE_INT_HDR.lstrip().split("\n")
    for idx, line1 in enumerate(output.split("\n")):
        line2 = sample_lines[idx]
        assert line1.strip() == line2.strip()


def test_float_header():
    volume = Volume.PROCESSED
    trace, _, scalar_event, _, _ = get_sample_data(volume)
    float_header = FloatHeader(trace, scalar_event, volume)
    cosmos_file = StringIO()
    float_header.write(cosmos_file)
    output = cosmos_file.getvalue()
    sample_lines = SAMPLE_FLOAT_HDR.lstrip().split("\n")
    output_lines = output.split("\n")
    for idx, line1 in enumerate(output_lines):
        line2 = sample_lines[idx]
        if line2.startswith("|<SCNL>"):
            continue
        assert line1.strip() == line2.strip()


def test_data_block():
    # test processed data block
    volume = Volume.PROCESSED
    trace, eventid, _, _, gmprocess_version = get_sample_data(volume)
    data_block = DataBlock(trace, volume, eventid, gmprocess_version)
    cosmos_file = StringIO()
    data_block.write(cosmos_file)
    output = cosmos_file.getvalue()
    output_lines = output.split("\n")
    print("\n".join(output_lines[0:20]))
    sample_lines = SAMPLE_DATA_BLOCK.lstrip().rstrip().split("\n")
    for idx, line1 in enumerate(sample_lines):
        line2 = output_lines[idx]
        if line2.startswith("|<SCNL>"):
            continue
        assert line1.strip() == line2.strip()

    # test raw data block
    volume = Volume.RAW
    trace, eventid, _, _, gmprocess_version = get_sample_data(volume)
    data_block = DataBlock(trace, volume, eventid, gmprocess_version)
    cosmos_file = StringIO()
    data_block.write(cosmos_file)
    output = cosmos_file.getvalue()
    output_lines = output.split("\n")
    print("\n".join(output_lines[0:20]))
    sample_lines = INT_SAMPLE_DATA_BLOCK.lstrip().rstrip().split("\n")
    for idx, line1 in enumerate(sample_lines):
        line2 = output_lines[idx]
        if line2.startswith("|<SCNL>"):
            continue
        assert line1.strip() == line2.strip()


def test_cosmos_writer(datafile=None):
    if datafile is None:
        # datafile = TEST_DATA_DIR / "asdf" / "nc71126864" / "workspace.h5"
        datafile = TEST_DATA_DIR / "data" / "asdf" / "nc71126864" / "workspace.h5"
    tempdir = None
    with tempfile.TemporaryDirectory() as tempdir:
        cosmos_writer = CosmosWriter(
            tempdir,
            datafile,
            volume=Volume.CONVERTED,
            label="default",
            concatenate_channels=True,
        )
        t1 = time.time()
        files, nevents, nstreams, ntraces = cosmos_writer.write()
        t2 = time.time()
        dt = t2 - t1
        msg = (
            f"{nevents} events, {nstreams} streams, "
            f"{ntraces} traces written: {dt:.2f} seconds"
        )
        print(msg)
        for tfile in files:

            assert is_cosmos(tfile)
            stream = read_cosmos(tfile)[0]
            print(stream[0].stats["starttime"])
            assert len(stream) == 3
            len(stream[0].data) == 12091
            assert stream[0].stats["starttime"] == UTCDateTime(
                2021, 12, 20, 20, 13, 55.850000
            )


if __name__ == "__main__":
    test_text_header()
    test_float_header()
    test_data_block()
    test_int_header()
    test_cosmos_writer()
