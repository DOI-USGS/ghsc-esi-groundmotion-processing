#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import numpy as np

from gmprocess.io.geonet.core import read_geonet
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.metrics.station_summary import StationSummary
from gmprocess.utils.base_utils import read_event_json_files
from gmprocess.utils.constants import TEST_DATA_DIR
from gmprocess.utils.config import get_config
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.waveform_processing.processing import process_streams


def test_stationsummary():
    datafiles, event = read_data_dir(
        "geonet", "us1000778i", "20161113_110259_WTMC_20.V2A"
    )
    datafile = datafiles[0]

    target_imcs = np.sort(
        ["GREATER_OF_TWO_HORIZONTALS", "H1", "H2", "Z", "ROTD(50.0)", "ROTD(100.0)"]
    )
    target_imts = np.sort(["SA(1.000)", "PGA", "PGV"])
    stream = read_geonet(datafile)[0]
    stream_summary = StationSummary.from_stream(
        stream,
        ["greater_of_two_horizontals", "channels", "rotd50", "rotd100", "invalid"],
        ["sa1.0", "PGA", "pgv", "invalid"],
        event,
    )
    stream_summary.starttime
    np.testing.assert_array_equal(np.sort(stream_summary.components), target_imcs)
    np.testing.assert_array_equal(np.sort(stream_summary.imts), target_imts)
    np.testing.assert_almost_equal(
        stream_summary.get_pgm("PGA", "H1"), 99.3173469387755, decimal=1
    )
    target_available = np.sort(
        [
            "greater_of_two_horizontals",
            "geometric_mean",
            "arithmetic_mean",
            "channels",
            "gmrotd",
            "rotd",
            "quadratic_mean",
            "radial_transverse",
        ]
    )
    imcs = stream_summary.available_imcs
    np.testing.assert_array_equal(np.sort(imcs), target_available)
    target_available = np.sort(
        ["pga", "pgv", "sa", "arias", "fas", "duration", "sorted_duration"]
    )
    imts = stream_summary.available_imts
    np.testing.assert_array_equal(np.sort(imts), target_available)
    test_pgms = {
        "PGV": {
            "ROTD(100.0)": 114.24894584734818,
            "ROTD(50.0)": 81.55436750525355,
            "Z": 37.47740000000001,
            "H1": 100.81460000000004,
            "H2": 68.4354,
            "GREATER_OF_TWO_HORIZONTALS": 100.81460000000004,
        },
        "PGA": {
            "ROTD(100.0)": 100.73875535385548,
            "ROTD(50.0)": 91.40178541935455,
            "Z": 183.7722361866693,
            "H1": 99.24999872535474,
            "H2": 81.23467239067368,
            "GREATER_OF_TWO_HORIZONTALS": 99.24999872535474,
        },
        "SA(1.000)": {
            "ROTD(100.0)": 146.9023350124098,
            "ROTD(50.0)": 106.03202302692158,
            "Z": 27.74118995438756,
            "H1": 136.25041187387063,
            "H2": 84.69296738413021,
            "GREATER_OF_TWO_HORIZONTALS": 136.25041187387063,
        },
    }
    pgms = stream_summary.pgms
    for imt_str in test_pgms:
        for imc_str in test_pgms[imt_str]:
            result = pgms.loc[imt_str, imc_str].Result
            np.testing.assert_almost_equal(
                result, test_pgms[imt_str][imc_str], decimal=10
            )

    # Test with fas
    stream = read_geonet(datafile)[0]
    stream_summary = StationSummary.from_stream(
        stream,
        ["greater_of_two_horizontals", "channels", "geometric_mean"],
        ["sa1.0", "PGA", "pgv", "fas2.0"],
        event,
    )
    target_imcs = np.sort(
        ["GEOMETRIC_MEAN", "GREATER_OF_TWO_HORIZONTALS", "H1", "H2", "Z"]
    )
    target_imts = np.sort(["SA(1.000)", "PGA", "PGV", "FAS(2.000)"])
    np.testing.assert_array_equal(np.sort(stream_summary.components), target_imcs)
    np.testing.assert_array_equal(np.sort(stream_summary.imts), target_imts)

    # Test config use
    stream = read_geonet(datafile)[0]
    config = get_config()
    config["metrics"]["sa"]["periods"]["defined_periods"] = [0.3, 1.0]
    stream_summary = StationSummary.from_config(stream, event=event, config=config)
    target_imcs = np.sort(["H1", "H2", "Z"])
    assert stream_summary.smoothing == "konno_ohmachi"
    assert stream_summary.bandwidth == 20.0
    assert stream_summary.damping == 0.05

    # test XML output
    stream = read_geonet(datafile)[0]
    imclist = ["greater_of_two_horizontals", "channels", "rotd50.0", "rotd100.0"]
    imtlist = ["sa1.0", "PGA", "pgv", "fas2.0", "arias"]
    stream_summary = StationSummary.from_stream(stream, imclist, imtlist, event=event)
    xmlstr = stream_summary.get_metric_xml()

    xml_station = stream_summary.get_station_xml()

    imc_dict = stream_summary.get_imc_dict("H2")
    assert list(imc_dict.keys()) == ["H2"]
    assert len(imc_dict["H2"]) == 38

    sa_array = stream_summary.get_sa_arrays("H1")
    assert list(sa_array.keys()) == ["H1"]
    assert "period" in sa_array["H1"].keys()
    assert "sa" in sa_array["H1"].keys()
    assert len(sa_array["H1"]["sa"]) == 2

    stream2 = StationSummary.from_xml(xmlstr, xml_station)
    cmp1 = np.sort(
        ["GREATER_OF_TWO_HORIZONTALS", "H1", "H2", "ROTD100.0", "ROTD50.0", "Z"]
    )
    cmp2 = np.sort(stream2.components)
    np.testing.assert_array_equal(cmp1, cmp2)
    imt1 = np.sort(stream_summary.imts)
    imt2 = np.sort(stream2.imts)
    np.testing.assert_array_equal(imt1, imt2)


def test_allow_nans():
    datadir = TEST_DATA_DIR / "fdsn" / "uu60363602"
    sc = StreamCollection.from_directory(datadir)
    event = read_event_json_files([str(datadir / "event.json")])[0]
    psc = process_streams(sc, event)
    st = psc[0]

    ss = StationSummary.from_stream(
        st,
        components=["quadratic_mean"],
        imts=["FAS(4.0)"],
        bandwidth=300,
        allow_nans=True,
        event=event,
    )
    assert np.isnan(ss.pgms.Result).all()

    ss = StationSummary.from_stream(
        st,
        components=["quadratic_mean"],
        imts=["FAS(4.0)"],
        bandwidth=189,
        allow_nans=False,
        event=event,
    )
    assert ~np.isnan(ss.pgms.Result).all()


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_stationsummary()
    test_allow_nans()
