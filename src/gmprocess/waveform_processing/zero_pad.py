"""Module for zero pad processing step."""

import inspect

import numpy as np

from gmprocess.waveform_processing.processing_step import processing_step
from gmprocess.waveform_processing.filtering import highpass_filter


@processing_step
def zero_pad(st, length="fhp", config=None):
    """Add zero pads to streams.

    Args:
        st (StationStream):
            Stream of data.
        length (float, str):
            The length (in sec) to pad with zeros before and after the trace, or "fhp"
            to compute the zero pad length from the filter order and the highpass
            corner as `1.5 * filter_order / flc`.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: Streams with the zero padding applied.
    """
    if not st.passed:
        return st

    use_fhp = False
    if length == "fhp":
        use_fhp = True
        psteps = list(config["processing"])
        filter_order = None
        # Getting filter order is a bit complicated. First check the config to see if it
        # is set there, and if not get the default value from the filter function.
        for pstep in psteps:
            if (
                ("highpass_filter" in pstep)
                and (pstep["highpass_filter"] is not None)
                and ("filter_order" in pstep["highpass_filter"])
            ):
                filter_order = pstep["highpass_filter"]["filter_order"]
        if filter_order is None:
            # If filter order is not set in config, then it will use the default
            # argument value.
            hp_sig = inspect.signature(highpass_filter)
            for func_arg, val in hp_sig.parameters.items():
                if func_arg == "filter_order":
                    filter_order = val.default

        # Need to use a consistent fhp for all traces in stream so that the number of
        # points is constant.
        fhps = []
        for tr in st:
            freq_dict = tr.get_parameter("corner_frequencies")
            fhps.append(freq_dict["highpass"])
        fhp = np.min(fhps)

    for tr in st:
        if tr.passed:
            if use_fhp:
                # Need to hand off half the length becasue it is added to both sides
                # (0.75 instead of 1.5, equation from Converse and Brady, 1992)
                length = 0.75 * filter_order / fhp
            tr.zero_pad(length=length)
    return st


@processing_step
def strip_zero_pad(st, config=None):
    """Remove zero pads from streams.

    Args:
        st (StationStream):
            Stream of data.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: Streams with the zero padding removed.
    """
    if not st.passed:
        return st

    for tr in st:
        tr.strip_zero_pad()

    return st
