"""Module for filtering processing steps."""

from gmprocess.waveform_processing.processing_step import processing_step


@processing_step
def bandpass_filter(
    st, frequency_domain=True, filter_order=5, number_of_passes=1, config=None
):
    """Apply the bandpass filter.

    Args:
        st (StationStream):
            Stream of data.
        frequency_domain (bool):
            If true, use gmprocess frequency domain implementation; if false, use ObsPy
            filters.
        filter_order (int):
            Filter order.
        number_of_passes (int):
            Number of passes.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: Stream with bandpass filter applied.
    """
    if not st.passed:
        return st

    for tr in st:
        if tr.stats.standard.units_type != "acc":
            tr.fail("Unit type must be acc to apply bandpass filter.")
            continue

        if tr.passed:
            tr = bandpass_filter_trace(
                tr, frequency_domain, filter_order, number_of_passes, config
            )

    return st


def bandpass_filter_trace(
    tr, frequency_domain=True, filter_order=5, number_of_passes=1, config=None
):
    """
    Bandpass filter.

    Args:
        tr (StationTrace):
            Stream of data.
        frequency_domain (bool):
            If true, use gmprocess frequency domain implementation; if false, use ObsPy
            filters.
        filter_order (int):
            Filter order.
        number_of_passes (int):
            Number of passes.
        config (dict):
            Dictionary containing configuration.

    Returns:
        StationTrace: Stream with bandpass filter applied.
    """
    if number_of_passes == 1:
        zerophase = False
    elif number_of_passes == 2:
        zerophase = True
    else:
        raise ValueError("number_of_passes must be 1 or 2.")
    try:
        freq_dict = tr.get_parameter("corner_frequencies")
        freqmin = freq_dict["highpass"]
        freqmax = freq_dict["lowpass"]

        tr.filter(
            type="bandpass",
            freqmin=freqmin,
            freqmax=freqmax,
            corners=filter_order,
            zerophase=zerophase,
            config=config,
            frequency_domain=frequency_domain,
        )

    except BaseException as e:
        tr.fail(f"Bandpass filter failed with excpetion: {e}")
    return tr


@processing_step
def highpass_filter(
    st, frequency_domain=True, filter_order=5, number_of_passes=1, config=None
):
    """Apply the highpass filter.

    Args:
        st (StationStream):
            Stream of data.
        frequency_domain (bool):
            If true, use gmprocess frequency domain implementation; if false, use ObsPy
            filters.
        filter_order (int):
            Filter order.
        number_of_passes (int):
            Number of passes.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: Stream with highpass filter applied.
    """
    if not st.passed:
        return st

    for tr in st:
        if tr.stats.standard.units_type != "acc":
            tr.fail("Unit type must be acc to apply highpass filter.")
            continue

        if tr.passed:
            tr = highpass_filter_trace(
                tr, frequency_domain, filter_order, number_of_passes, config
            )

    return st


def highpass_filter_trace(
    tr, frequency_domain=True, filter_order=5, number_of_passes=1, config=None
):
    """
    Highpass filter.

    Args:
        tr (StationTrace):
            Stream of data.
        frequency_domain (bool):
            If true, use gmprocess frequency domain implementation; if false, use ObsPy
            filters.
        filter_order (int):
            Filter order.
        number_of_passes (int):
            Number of passes.
        config (dict):
            Dictionary containing configuration.

    Returns:
        StationTrace: Stream with highpass filter applied.
    """
    if number_of_passes == 1:
        zerophase = False
    elif number_of_passes == 2:
        zerophase = True
    else:
        raise ValueError("number_of_passes must be 1 or 2.")
    try:
        freq_dict = tr.get_parameter("corner_frequencies")
        freq = freq_dict["highpass"]

        tr.filter(
            type="highpass",
            freq=freq,
            corners=filter_order,
            zerophase=zerophase,
            config=config,
            frequency_domain=frequency_domain,
        )

    except BaseException as e:
        tr.fail(f"Highpass filter failed with excpetion: {e}")
    return tr


@processing_step
def lowpass_filter(
    st, frequency_domain=True, filter_order=5, number_of_passes=1, config=None
):
    """Apply the lowpass filter.

    Args:
        st (StationStream):
            Stream of data.
        frequency_domain (bool):
            If true, use gmprocess frequency domain implementation; if false, use ObsPy
            filters.
        filter_order (int):
            Filter order.
        number_of_passes (int):
            Number of passes.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: Filtered streams.
    """
    if not st.passed:
        return st

    for tr in st:
        if tr.stats.standard.units_type != "acc":
            tr.fail("Unit type must be acc to apply lowpass filter.")
            continue

        if tr.passed:
            tr = lowpass_filter_trace(
                tr, frequency_domain, filter_order, number_of_passes, config
            )

    return st


def lowpass_filter_trace(
    tr, frequency_domain=True, filter_order=5, number_of_passes=1, config=None
):
    """
    Lowpass filter.

    Args:
        tr (StationTrace):
            Stream of data.
        frequency_domain (bool):
            If true, use gmprocess frequency domain implementation; if false, use ObsPy
            filters.
        filter_order (int):
            Filter order.
        number_of_passes (int):
            Number of passes.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationTrace: Filtered trace.
    """
    if number_of_passes == 1:
        zerophase = False
    elif number_of_passes == 2:
        zerophase = True
    else:
        raise ValueError("number_of_passes must be 1 or 2.")

    freq_dict = tr.get_parameter("corner_frequencies")
    freq = freq_dict["lowpass"]
    try:
        tr.filter(
            type="lowpass",
            freq=freq,
            corners=filter_order,
            zerophase=zerophase,
            config=config,
            frequency_domain=frequency_domain,
        )

    except BaseException as e:
        tr.fail(f"Lowpass filter failed with exception: {e}")
    return tr
