"""Module for Rotd class."""

# Local imports
from gmprocess.metrics.rotation.rotation import Rotation


class Rotd(Rotation):
    """Class for computing the ROTD rotation."""

    def __init__(self, rotation_data, event=None):
        """
        Args:
            rotation_data (obspy.core.stream.Stream or numpy.ndarray):
                Intensity measurement component.
            event (ScalarEvent):
                Defines the focal time, geographical location and magnitude of
                an earthquake hypocenter. Default is None.
        """
        super().__init__(rotation_data, event=event)
        self.result = self.get_rotd()

    def get_rotd(self):
        """
        Performs ROTD rotation.

        Returns:
            StationStreams with rotated data added to stream parameters with
            id "rotd".
        """
        streams = self.rotation_data.copy()
        horizontals = self._get_horizontals()
        osc1, osc2 = horizontals[0].data, horizontals[1].data
        rotd = [self.rotate(osc1, osc2, combine=True)]
        streams.set_stream_param("rotated", rotd)
        if horizontals[0].has_cached("upsampled"):
            up_osc1 = horizontals[0].get_cached("upsampled")["data"]
            up_osc2 = horizontals[1].get_cached("upsampled")["data"]
            up_rotd = [self.rotate(up_osc1, up_osc2, combine=True)]
            streams.set_stream_param("upsampled_rotated", up_rotd)
        return streams
