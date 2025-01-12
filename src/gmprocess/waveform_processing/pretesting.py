"""Module for 'pretesting' processing steps."""

import logging
from obspy.signal.trigger import classic_sta_lta
from gmprocess.utils.config import get_config
from gmprocess.waveform_processing.processing_step import processing_step


@processing_step
def min_sample_rate(st, min_sps=20.0, config=None):
    """Require a minimum sample rate.

    Args:
        st (gmprocess.core.stationstream.StationStream):
            Stream of data.
        min_sps (float):
            Minimum samples per second.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: Stream checked for sample rate criteria.
    """
    if not st.passed:
        return st

    for tr in st:
        if tr.passed:
            actual_sps = tr.stats.sampling_rate
            if actual_sps < min_sps:
                tr.fail(f"Minimum sample rate of {min_sps} not exceeded.")

    return st


@processing_step
def check_instrument(st, n_max=3, n_min=2, require_two_horiz=True, config=None):
    """Test the channels of the station.

    The purpose of the maximum limit is to skip over stations with muliple
    strong motion instruments, which can occur with downhole or structural
    arrays since our code currently is not able to reliably group by location
    within an array.

    The purpose of the minimum and require_two_horiz checks are to ensure the
    channels are required for subsequent intensity measures such as ROTD.

    Args:
        st (gmprocess.core.stationstream.StationStream):
            Stream of data.
        n_max (int):
            Maximum allowed number of streams; default to 3.
        n_min (int):
            Minimum allowed number of streams; default to 1.
        require_two_horiz (bool):
            Require two horizontal components; default to `False`.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: Stream with instrument criteria applied.
    """
    if not st.passed:
        return st

    if config is None:
        config = get_config()

    for failed_test, message in [
        (len(st) > n_max, f"More than {n_max} traces in stream."),
        (len(st) < n_min, f"Less than {n_min} traces in stream."),
        (
            require_two_horiz and (st.num_horizontal != 2),
            "Stream requires two horizontal components.",
        ),
    ]:
        if failed_test:
            for tr in st:
                tr.fail(message)
            # Stop at first failed test
            break

    return st


@processing_step
def check_free_field(st, reject_non_free_field=True, config=None):
    """Checks free field status of stream.

    Args:
        st (gmprocess.core.stationstream.StationStream):
            Stream of data.
        reject_non_free_field (bool):
            Should non free-field stations be failed?
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: Stream that has been checked for free field status.
    """
    if not st.passed:
        return st

    for trace in st:
        if trace.passed and not trace.free_field and reject_non_free_field:
            trace.fail("Failed free field sensor check.")

    return st


@processing_step
def check_sta_lta(st, sta_length=1.0, lta_length=20.0, threshold=5.0, config=None):
    """Apply STA/LTA ratio criteria.

    Checks that the maximum STA/LTA ratio of the stream's traces is above a threshold.

    Args:
        st (gmprocess.core.stationstream.StationStream):
            Stream of data.
        sta_length (float):
            Length of time window for STA (seconds).
        lta_length (float):
            Length of time window for LTA (seconds).
        threshold (float):
            Required maximum STA/LTA ratio to pass the test.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: Stream that has been checked for sta/lta requirements.
    """
    if not st.passed:
        return st

    for tr in st:
        if tr.passed:
            sr = tr.stats.sampling_rate
            nlta = lta_length * sr + 1
            if len(tr) >= nlta:
                sta_lta = classic_sta_lta(tr.data, sta_length * sr + 1, nlta)
                if sta_lta.max() < threshold:
                    tr.fail(
                        "Failed sta/lta check because threshold sta/lta is not "
                        "exceeded."
                    )
            else:
                tr.fail(
                    "Failed sta/lta check because record length is shorter "
                    "than lta length."
                )

    return st


@processing_step
def check_max_amplitude(st, min=5, max=2e6, config=None):
    """Check the maximum amplitude of the traces.

    Checks that the maximum amplitude of the traces in the stream are within a defined
    range. Only applied to counts/raw data. This is a simple way to screen for clipped
    records, but we now recommend/prefer the `check_clipping` method.

    Args:
        st (gmprocess.core.stationstream.StationStream):
            Stream of data.
        min (float):
            Minimum amplitude for the acceptable range. Default is 5.
        max (float):
            Maximum amplitude for the acceptable range. Default is 2e6.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: Stream that has been checked for maximum amplitude criteria.
    """
    if not st.passed:
        return st

    for tr in st:
        # Only perform amplitude/clipping check if data has not been converted
        # to physical units
        if tr.passed:
            if "remove_response" not in tr.provenance.ids:
                if abs(tr.max()) < float(min) or abs(tr.max()) > float(max):
                    tr.fail("Failed max amplitude check.")

    return st


@processing_step
def max_traces(st, n_max=3, config=None):
    """Reject a stream if it has more than n_max traces.

    The purpose of this is to skip over stations with muliple strong motion
    instruments, which can occur with downhole or structural arrays since our
    code currently is not able to reliably group by location within an array.

    Args:
        st (gmprocess.core.stationstream.StationStream):
            Stream of data.
        n_max (int):
            Maximum allowed number of streams; default to 3.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: Stream with max number of traces criteria applied.
    """
    logging.warning(
        "This function is deprecated. Please replace with "
        "check_instrument, which includes additional "
        "functionality."
    )
    if not st.passed:
        return st

    if len(st) > n_max:
        for tr in st:
            tr.fail(f"More than {n_max} traces in stream.")
    return st
