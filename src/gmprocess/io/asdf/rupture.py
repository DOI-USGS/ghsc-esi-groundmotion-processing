"""Module for adding rupture to ASDF file."""

import json

from esi_utils_rupture.point_rupture import PointRupture
from esi_utils_rupture.origin import Origin
from esi_utils_rupture.factory import get_rupture

from gmprocess.subcommands.lazy_loader import LazyLoader

origin = LazyLoader("rupt", globals(), "esi_utils_rupture.origin")


class Rupture(object):
    """Class for populating the cells and vertices from the rupture in the ASDF file."""

    def __init__(self, vertices, cells, description, reference):
        self.vertices = vertices
        self.cells = cells
        self.description = description
        self.reference = reference

    @classmethod
    def from_shakemap(cls, rupture_file, event=None):
        """Generates rupture model info for workspace from shakemap rupture.json file.

        Parameters
        ----------
        rupture_file : str
            String representation of the rupture file path for an event.
        event : Event, optional
            Obspy event object.

        Returns
        -------
        vertices: 2D list
            List of lists, inner lists are the x,y,z for each vertex
            in the rupture model.
        cells: 2D list
            List of lists, inner lists contain the indices corresponding
            to the vertices that build a given cell in the rupture model.
        description: str
            Description of model.
        reference: str
            Source of rupture model.
        """

        def find_point_coordinate(coordinate):
            """Recursive function that identifies list of x,y,z defining the coordinate
               for a point rupture.

            Parameters
            ----------
            coordinate : list (maybe multi-dimensional)
                N-dimensional list which only contains a single coordinate.

            Returns
            -------
            coordinate
               1-dimensional list containing the x,y,z of a coordinate.

            Raises
            ------
            Exception
                This exception tries to catch the possible case that "coordinate"
                is never a list of length 3, meaning the coordinate is not in an
                expected format.
            """
            if len(coordinate) == 3:
                return coordinate
            else:
                try:
                    coordinate = coordinate[0]
                    coordinate = find_point_coordinate(coordinate)
                except BaseException:
                    raise Exception(
                        "Could not identify a list of [x, y, z] for point rupture coordinate in rupture.json"
                    )

        vertices = []
        cells = []

        # actual event information is not needed to generate origin and read rupture file
        if event is not None:
            origin_obj = Origin(
                {
                    "id": event.origins[0].resource_id.id.replace("smi:local/", ""),
                    "netid": "",
                    "network": "",
                    "lat": event.latitude,
                    "lon": event.longitude,
                    "depth": event.depth_km,
                    "locstring": "",
                    "mag": event.magnitude,
                    "time": event.time,
                }
            )
        else:
            origin_obj = Origin(
                {
                    "id": "",
                    "netid": "",
                    "network": "",
                    "lat": 0,
                    "lon": 0,
                    "depth": 0,
                    "locstring": "",
                    "mag": 0,
                    "time": "",
                }
            )

        with open(rupture_file, encoding="utf-8") as fin:
            rupture_json = json.load(fin)
        reference = rupture_json["metadata"]["reference"]
        description = reference  # for now

        rupture = get_rupture(origin_obj, file=rupture_file)

        if isinstance(rupture, PointRupture):
            coordinate = rupture_json["features"][0]["geometry"]["coordinates"]
            coordinate = find_point_coordinate(coordinate)

            vertices.append([coordinate[0], coordinate[1], coordinate[2]])
            cells.append([0])

        else:
            i_vertex = 0
            for quad in rupture.getQuadrilaterals():
                cell = []
                for vertex in quad:
                    vertices.append([vertex.x, vertex.y, vertex.z])
                    cell.append(i_vertex)
                    i_vertex += 1
                cells.append(cell)

        return cls(vertices, cells, description, reference)


# gmprocess currently doesn't support having the finite fault rupture, so we are not implementing just yet

# @classmethod
# def from_finite_fault(cls, event, rupture_file):

#     vertices = []
#     cells = []

#     return cls(vertices, cells)

# "to" methods to be populated later

# def to_shakemap(self):
#     rupture_file = ""

#     return rupture_file
