#!/usr/bin/env python

from gmprocess.io.asdf.stream_workspace import StreamWorkspace
import numpy as np

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


def get_rupture_prep(eventid):
    file_loc = Path(__file__)
    test_data_loc = file_loc.parent.parent.parent.parent / "data" / "asdf" / "rupture" / eventid
    ws = StreamWorkspace(test_data_loc / "workspace.h5")

    event_ids = ws.get_event_ids()
    eventid = event_ids[0]
    event_obj = ws.get_event(eventid)

    rupture = ws.get_rupture(event_obj)

    cells = rupture["cells"]
    cells_size = np.size(cells)

    vertices = rupture["vertices"]
    vertices_size = np.size(vertices)

    description = rupture["description"]
    reference = rupture["reference"]

    return cells_size, vertices_size, description, reference


def test_get_rupture_quad():
    # this rupture file contains multiple polygons that each have 5 vertices (with the first and last being the same)

    cells_size, vertices_size, description, reference = get_rupture_prep("us1000778i")

    assert cells_size == 44  # num vertices
    assert vertices_size == 132  # num vertices * 3
    assert description == "Source: Bradley et al (2017) Ground motion Observations from the 14 November 1 2016 Mw7.8 Kaikoura, New Zealand earthquake"
    assert reference == "Source: Bradley et al (2017) Ground motion Observations from the 14 November 1 2016 Mw7.8 Kaikoura, New Zealand earthquake"

def test_get_rupture_complex():
    # this rupture file contains seven polygons, two of which have more than 5 vertices (they have 7 vertices)

    cells_size, vertices_size, description, reference = get_rupture_prep("usp0009d4z")

    assert cells_size == 36  # num vertices
    assert vertices_size == 108  # num vertices * 3
    assert description == "SOURCE: Barka, A., H. S. AkyÃ¼z, E. Altunel, G. Sunal, Z. Ã\x87akir, A. Dikbas, B. Yerli, R. Armijo, B. Meyer, J. B. d. Chabalier, T. Rockwell, J. R. Dolan, R. Hartleb, T. Dawson, S. Christofferson, A. Tucker, T. Fumal, R. Langridge, H. Stenner, W. Lettis, J. Bachhuber, and W. Page (2002). The Surface Rupture and Slip Distribution of the 17 August 1999 Izmit Earthquake (M 7.4), North Anatolian Fault, Bull. Seism. Soc. Am. 92, 43-60."
    assert reference == "SOURCE: Barka, A., H. S. AkyÃ¼z, E. Altunel, G. Sunal, Z. Ã\x87akir, A. Dikbas, B. Yerli, R. Armijo, B. Meyer, J. B. d. Chabalier, T. Rockwell, J. R. Dolan, R. Hartleb, T. Dawson, S. Christofferson, A. Tucker, T. Fumal, R. Langridge, H. Stenner, W. Lettis, J. Bachhuber, and W. Page (2002). The Surface Rupture and Slip Distribution of the 17 August 1999 Izmit Earthquake (M 7.4), North Anatolian Fault, Bull. Seism. Soc. Am. 92, 43-60."

def test_get_rupture_point():
    # this rupture file is a point rupture

    cells_size, vertices_size, description, reference = get_rupture_prep("us7000kg9g")

    assert cells_size == 1  # num vertices
    assert vertices_size == 3  # num vertices * 3
    assert description == "Origin"
    assert reference == "Origin"


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_rupture_quad()
    test_rupture_edge()
    test_rupture_complex()
    test_rupture_point()
    test_get_rupture_quad()
    test_get_rupture_complex()
    test_get_rupture_point()