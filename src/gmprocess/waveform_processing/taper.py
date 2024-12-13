"""Module for tapering functions."""

from gmprocess.waveform_processing.processing_step import processing_step


@processing_step
def taper(st, type="hann", width=0.05, side="both", config=None):
    """Taper streams.

    Args:
        st (StationStream):
            Stream of data.
        type (str):
            Taper type.
        width (float):
            Taper width as percentage of trace length.
        side (str):
            Valid options: "both", "left", "right".
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: Stream with the taper applied.
    """
    if not st.passed:
        return st

    for tr in st:
        if tr.passed:
            tr.taper(max_percentage=width, type=type, side=side)
    return st
