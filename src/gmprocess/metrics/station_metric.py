"""Module for the StationMetric class."""

from dataclasses import dataclass


@dataclass
class StationMetric:
    """Data class for storing a station metric parameters.

    Note that there is no "from_dict" method since initializing the class from a
    dictionary (as long as it isn't nested) is very easy:

    sta_metric = StationMetric(**a_dict)
    """

    repi: float
    rhyp: float
    rrup_mean: float
    rrup_var: float
    rjb_mean: float
    rjb_var: float
    gc2_rx: float
    gc2_ry: float
    gc2_ry0: float
    gc2_U: float
    gc2_T: float
    back_azimuth: float

    def to_dict(self):
        """Convenience method to convert to a dictionary.

        Note that since this dataclass does not have any nesting, there's no need to use
        the "asdict" method, which is supposedly much slower.
        """
        return self.__dict__
