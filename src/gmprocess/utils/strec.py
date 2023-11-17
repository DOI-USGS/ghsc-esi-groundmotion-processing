"""Module for handling STREC queries and results."""

import json

from strec.subtype import SubductionSelector


class STREC(object):
    """Class for handling STREC queries and results."""

    def __init__(self, strec_results):
        """Initialize STREC object.

        Args:
            strec_results (dict):
                Dictionary containing STREC results.
        """
        self.results = strec_results

    @classmethod
    def from_file(cls, filename):
        """Read STREC results from a file.

        Args:
            filename (str):
                File containing STREC results.
        """
        with open(filename, encoding="utf-8") as f:
            strec_dict = json.load(f)
        return cls(strec_dict)

    @classmethod
    def from_event(cls, event):
        """Get STREC results from an event object.

        Args:
            event (utils.event.ScalarEvent):
                A gmprocess ScalarEvent object.
        """
        selector = SubductionSelector()
        tensor_params = None
        if hasattr(event, "id"):
            _, _, _, _, tensor_params = selector.getOnlineTensor(event.id)
        strec_dict = selector.getSubductionType(
            event.latitude,
            event.longitude,
            event.depth_km,
            event.magnitude,
            eventid=event.id,
            tensor_params=tensor_params,
        ).to_dict()
        return cls(strec_dict)

    def to_file(self, filename):
        """Write STREC results to a file.

        Args:
            filename (str):
                Location to write STREC results.
        """
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.results, f)
