"""Module for the clipping detection method."""

import numpy as np

from obspy.geodetics.base import gps2dist_azimuth

from gmprocess.waveform_processing.clipping.clipping_ann import clipNet
from gmprocess.waveform_processing.clipping.max_amp import MaxAmp
from gmprocess.waveform_processing.clipping.histogram import Histogram
from gmprocess.waveform_processing.clipping.ping import Ping
from gmprocess.waveform_processing.processing_step import processing_step

M_TO_KM = 1.0 / 1000


@processing_step
def check_clipping(st, event, threshold=0.2, config=None):
    """Apply clipping check.

    Lower thresholds will pass fewer streams but will give less false negatives
    (i.e., streams in which clipping actually occurred but were missed).

    Args:
        st (gmprocess.core.stationstream.StationStream):
           Trace of data.
        event (gmprocess.utils.scalar_event.ScalarEvent):
            ScalarEvent object.
        threshold (float):
            Threshold probability.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: With clipping check applied.

    """

    # Don't bother with test if it has already failed
    if not st.passed:
        return st

    event_mag = event.magnitude
    event_lon = event.longitude
    event_lat = event.latitude
    dist = (
        gps2dist_azimuth(
            lat1=event_lat,
            lon1=event_lon,
            lat2=st[0].stats["coordinates"]["latitude"],
            lon2=st[0].stats["coordinates"]["longitude"],
        )[0]
        * M_TO_KM
    )

    # Clip mag/dist to range of training dataset
    event_mag = np.clip(event_mag, 4.0, 8.8)
    dist = np.clip(dist, 0.0, 445.0)

    clip_nnet = clipNet()

    max_amp_method = MaxAmp(st, max_amp_thresh=6e6)
    hist_method = Histogram(st)
    ping_method = Ping(st)
    inputs = [
        event_mag,
        dist,
        max_amp_method.is_clipped,
        hist_method.is_clipped,
        ping_method.is_clipped,
    ]
    prob_clip = clip_nnet.evaluate(inputs)[0][0]

    for tr in st:
        tr.set_parameter("clipping_probability", {"probability": prob_clip})
        if prob_clip >= threshold:
            tr.fail("Failed clipping check.")

    return st
