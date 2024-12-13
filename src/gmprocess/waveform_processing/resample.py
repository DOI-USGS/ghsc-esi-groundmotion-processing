"""Module for resampling processing steps."""

from gmprocess.waveform_processing.processing_step import processing_step


@processing_step
def resample(st, new_sampling_rate=None, method=None, a=None, config=None):
    """Resample stream.

    Args:
        st (StationStream):
            Stream of data.
        new_sampling_rate (float):
            New sampling rate, in Hz.
        method (str):
            Method for interpolation. Currently only supports 'lanczos'.
        a (int):
            Width of the Lanczos window, in number of samples.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: Stream with resampling applied.
    """
    if not st.passed:
        return st

    if method != "lanczos":
        raise ValueError("Only lanczos interpolation method is supported.")

    for tr in st:
        if tr.passed:
            tr.interpolate(sampling_rate=new_sampling_rate, method=method, a=a)
            tr.set_provenance("resample", {"new_sampling_rate": new_sampling_rate})

    return st
