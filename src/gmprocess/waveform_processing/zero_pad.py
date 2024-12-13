"""Module for zero pad processing step."""

from gmprocess.waveform_processing.processing_step import processing_step


@processing_step
def zero_pad(st, length, config=None):
    """Taper streams.

    Args:
        st (StationStream):
            Stream of data.
        length (str):
            The length (in sec) to padd with zeros before and after the trace.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: With the zero padding applied.
    """
    if not st.passed:
        return st

    for tr in st:
        if tr.passed:
            tr.zero_pad(length=length)
    return st
