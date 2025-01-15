"""Module for the ScalarEvent class."""

import logging
import json
import io

import h5py

import obspy
from obspy.core.event.event import Event
from obspy.core.event.magnitude import Magnitude
from obspy.core.event.origin import Origin

from gmprocess.utils import constants


class ScalarEvent(Event):
    """Class to represent a flattened Event with only 1 origin and 1 magnitude.

    Note that depth in obspy's Origin object is in meters, but we use km.

    Also, be careful because we have a similar object with the same name:
    esi_utils_rupture.origin.Origin.

    """

    @classmethod
    def from_obspy(cls, event):
        """Create a ScalarEvent from an obspy Event object.

        Args:
            event (obspy.core.event.event.Event):
                And obspy Event object.
        """
        eventobj = cls()

        # copy the arrays
        for origin in event.origins:
            origin_copy = origin.copy()
            origin_copy.resource_id = origin_copy.resource_id.id.replace(
                "smi:local/", ""
            )
            eventobj.origins.append(origin_copy)
        for magnitude in event.magnitudes:
            eventobj.magnitudes.append(magnitude.copy())
        for station_magnitude in event.station_magnitudes:
            eventobj.station_magnitudes.append(station_magnitude.copy())
        for focal_mechanism in event.focal_mechanisms:
            eventobj.focal_mechanisms.append(focal_mechanism.copy())
        for amplitude in event.amplitudes:
            eventobj.amplitudes.append(amplitude.copy())
        for pick in event.picks:
            eventobj.picks.append(pick.copy())
        for comment in event.comments:
            eventobj.comments.append(comment.copy())
        for event_description in event.event_descriptions:
            eventobj.event_descriptions.append(event_description.copy())

        # copy the scalar stuff
        if event.creation_info is not None:
            eventobj.creation_info = event.creation_info.copy()
        if event.resource_id is not None:
            eventobj.resource_id = event.resource_id.copy()
        eventobj.event_type = event.event_type
        eventobj.event_type_certainty = event.event_type_certainty

        return eventobj

    @classmethod
    def from_params(
        cls, id, time, latitude, longitude, depth_km, magnitude, magnitude_type=None
    ):
        """Create a ScalarEvent (subclass of Event).

        Args:
            id (str):
                Desired ID for the event, usually ComCat ID.
            time (UTCDateTime):
                Origin time of the event.
            latitude (float):
                Latitude of origin.
            longitude (float):
                Longitude of origin.
            depth_km (float):
                Depth of origin in **kilometers**.
            magnitude (float):
                Magnitude of earthquake.
            magnitude_type (str):
                Magnitude type of earthquake.
        """
        event = cls()
        if isinstance(time, str):
            try:
                time = obspy.UTCDateTime(time)
            except BaseException as err:
                logging.info("Can not make UTCDateTime from string.")
                raise err

        # Convert depth to m for obspy's origin object
        origin = Origin(
            resource_id=id,
            time=time,
            longitude=longitude,
            latitude=latitude,
            depth=depth_km * 1000,
        )

        event.origins = [origin]

        mtype = (
            magnitude_type
            if magnitude_type != "unknown" and magnitude_type != ""
            else None
        )
        magnitude = Magnitude(resource_id=id, mag=magnitude, magnitude_type=mtype)
        event.magnitudes = [magnitude]
        event.resource_id = id
        return event

    @classmethod
    def from_workspace(cls, filename):
        """Create a ScalarEvent (subclass of Event) from QuakeML dataset in workspace file."""
        with h5py.File(filename) as h5:
            catalog = obspy.read_events(io.BytesIO(h5["QuakeML"][:]))
        if len(catalog) != 1:
            raise IOError(f"Expected a single event in QuakeML dataset in {filename}.")
        event = catalog[0]
        return ScalarEvent.from_obspy(event)

    @classmethod
    def from_json(cls, filename):
        def geojson_to_event(data):
            return {
                "id": data["id"],
                "time": obspy.UTCDateTime(data["properties"]["time"] / 1000.0),
                "latitude": data["geometry"]["coordinates"][1],
                "longitude": data["geometry"]["coordinates"][0],
                "depth_km": data["geometry"]["coordinates"][2],
                "magnitude": data["properties"]["mag"],
                "magnitude_type": data["properties"].get("magType", None),
            }

        def json_to_event(data):
            return {
                "id": data["id"],
                "time": data["time"],
                "latitude": data["latitude"],
                "longitude": data["longitude"],
                "depth_km": data["depth_km"],
                "magnitude": data["magnitude"],
                "magnitude_type": data.get("magnitude_type", None),
            }

        """Create a ScalarEvent (subclass of Event) from event geojson file."""
        if isinstance(filename, dict):
            # This is just a workaround so that we can hand off the dictionary returned
            # by `download_comcat_event` without having to write it to a file. This is
            # helpful for the tutorial in the documentation.
            data = filename
        else:
            with open(filename, "rt", encoding="utf-8") as fin:
                data = json.load(fin)
        if "properties" in data:
            event_values = geojson_to_event(data)
        else:
            event_values = json_to_event(data)
        return ScalarEvent.from_params(**event_values)

    def __repr__(self):
        if not hasattr(self, "origins") or not hasattr(self, "magnitudes"):
            return "Empty ScalarEvent"
        return f"{self.id} {str(self.time)} {self.latitude:.3f} {self.longitude:.3f} {self.depth_km:.1f}km M{self.magnitude:.2f} {self.magnitude_type}"

    def _get_origin(self):
        origin = self.preferred_origin()
        if origin is None:
            origin = self.origins[0]
        return origin

    def _get_magnitude(self):
        magnitude = self.preferred_magnitude()
        if magnitude is None:
            magnitude = self.magnitudes[0]
        return magnitude

    @property
    def id(self):
        """Return the origin resource_id."""
        origin = self._get_origin()
        return origin.resource_id.id

    @property
    def time(self):
        """Return the origin time."""
        origin = self._get_origin()
        return origin.time

    @property
    def latitude(self):
        """Return the origin latitude."""
        origin = self._get_origin()
        return origin.latitude

    @property
    def longitude(self):
        """Return the origin longitude."""
        origin = self._get_origin()
        return origin.longitude

    @property
    def depth_km(self):
        """Return the origin depth."""
        origin = self._get_origin()
        return origin.depth / 1000

    @property
    def magnitude(self):
        """Return the magnitude value."""
        magnitude = self._get_magnitude()
        return magnitude.mag

    @property
    def magnitude_type(self):
        """Return the magnitude type."""
        return self.magnitudes[0]["magnitude_type"]

    def to_json(self, event_dir):
        """Write event information to a JSON file in given event directory.

        Args:
            event_dir (Path):
                Event directory.
        """
        filename = event_dir / constants.EVENT_FILE
        data = {
            "id": self.id,
            "time": str(self.time),
            "latitude": self.latitude,
            "longitude": self.longitude,
            "depth_km": self.depth_km,
            "magnitude": self.magnitude,
            "magnitude_type": self.magnitude_type,
        }
        logging.info(f"Creating event file: {filename}")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f)


def get_events_from_file(filename=None):
    """Get the list of event ids to perform processing and events if provided in filename.

    Args:
        filename (str):
            Name of CSV file with event ids (single column) or event information (one event per row).

    Returns:
        Tuple with list of event ids and events (if provided).
    """

    def _parse_events_file(filename):
        """Parse event files that either contain event ids (1 per line) or event information (6 columns).

        Args:
            filename (Path):
                Name of events file.
        Returns:
            List of event ids or ScalarEvent.
        """
        with open(filename, encoding="utf-8") as fin:
            lines = fin.readlines()
        if len(lines[0].split(",")) == 1:
            event_info = [line.strip() for line in lines]
        else:
            event_info = []
            for line in lines:
                fields = line.split(",")
                if len(fields) != 7:
                    raise IOError(
                        f"Expected 7 columns in events file '{filename}'. Error parsing line '{line}'."
                    )
                event_values = {
                    "id": fields[0].strip(),
                    "time": fields[1].strip(),
                    "latitude": float(fields[2]),
                    "longitude": float(fields[3]),
                    "depth_km": float(fields[4]),
                    "magnitude": float(fields[5]),
                    "magnitude_type": fields[6].strip(),
                }
                event_info.append(ScalarEvent.from_params(**event_values))
        return event_info

    event_ids = None
    events = None
    if filename:
        events = _parse_events_file(filename)
        if len(events) and isinstance(events[0], ScalarEvent):
            event_ids = [event.id for event in events]
        else:
            event_ids = events
            events = [None] * len(event_ids)
    return (event_ids, events)


def get_event_ids(ids=None, file_ids=None, data_dir=None):
    """Get the list of event ids to perform processing.

    Order of precedence:
        1. List of event ids as given by `ids`.
        2. Event ids from a user provided file.
        3. Data directory containing event ids as subdirectories.

    Args:
        ids (list):
            List of event ids specified by a user.
        file_ids (list):
            List of event ids from a user provided file.
        data_dir (str):
            Name of directory containing event ids as subdirectories.

    Returns:
        List of event ids to use in processing.
    """
    event_ids = ids or file_ids
    if event_ids:
        if isinstance(event_ids, str):
            if "," in event_ids:
                event_ids = [eid.strip() for eid in event_ids.split(",")]
            else:
                event_ids = [event_ids]
    elif data_dir:
        event_ids = [ev_id.name for ev_id in data_dir.iterdir() if ev_id.is_dir()]
        event_ids = sorted(event_ids)
    else:
        raise ValueError(
            "Could not get a list of event ids. No event ids, file name, or data directory specified."
        )

    return event_ids


def write_geojson(data, event_dir):
    """Write event information to a GeoJSON file in given event directory.

    Args:
        data (dict):
            Event information.
        event_dir (Path):
            Event directory.
    """
    filename = event_dir / constants.EVENT_FILE
    logging.info(f"Creating event file: {filename}")
    with open(filename, "w", encoding="utf-8") as fout:
        json.dump(data, fout)
