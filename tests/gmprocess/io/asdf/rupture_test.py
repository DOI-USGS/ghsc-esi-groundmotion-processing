#!/usr/bin/env python

import os
from pathlib import Path
# from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.io.asdf.rupture import Rupture

def test_rupture_quad():
    # this rupture file contains multiple polygons that each have 5 vertices (with the first and last being the same)
    file_loc = Path(__file__)
    test_data_loc = file_loc.parent.parent.parent.parent / "data" / "asdf" / "rupture"
    myRupture = Rupture.from_shakemap(str(test_data_loc / "ruptureNewZealand.json"))

    assert len(myRupture.vertices) == 44
    assert len(myRupture.cells) == 11

def test_rupture_edge():
    # this rupture file contains one large polygon with 38 vertices
    file_loc = Path(__file__)
    test_data_loc = file_loc.parent.parent.parent.parent / "data" / "asdf" / "rupture"
    myRupture = Rupture.from_shakemap(str(test_data_loc / "ruptureCascadia.json"))

    assert len(myRupture.vertices) == 72
    assert len(myRupture.cells) == 18

def test_rupture_complex():
    # this rupture file contains seven polygons, two of which have more than 5 vertices (they have 7 vertices)
    file_loc = Path(__file__)
    test_data_loc = file_loc.parent.parent.parent.parent / "data" / "asdf" / "rupture"
    myRupture = Rupture.from_shakemap(str(test_data_loc / "ruptureIzmit.json"))

    assert len(myRupture.vertices) == 36
    assert len(myRupture.cells) == 9

def test_rupture_point():
    # this rupture file is a point rupture
    file_loc = Path(__file__)
    test_data_loc = file_loc.parent.parent.parent.parent / "data" / "asdf" / "rupture"
    myRupture = Rupture.from_shakemap(str(test_data_loc / "ruptureArgentina.json"))

    assert len(myRupture.vertices) == 1
    assert len(myRupture.cells) == 1

if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_rupture_quad()
    test_rupture_edge()
    test_rupture_complex()