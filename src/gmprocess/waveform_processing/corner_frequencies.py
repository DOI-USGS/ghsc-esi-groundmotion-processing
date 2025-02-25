"""Module for processing steps related to corner frequencies."""

import logging
import numpy as np

from gmprocess.waveform_processing.processing_step import processing_step
from gmprocess.waveform_processing.snr import compute_snr_trace

# Options for tapering noise/signal windows
TAPER_WIDTH = 0.05
TAPER_TYPE = "hann"
TAPER_SIDE = "both"


@processing_step
def get_corner_frequencies(
    st,
    event,
    method="snr",
    constant={"highpass": 0.08, "lowpass": 20.0},
    snr={"same_horiz": True},
    magnitude={
        "minmag": [-999.0, 3.5, 5.5],
        "highpass": [0.5, 0.3, 0.1],
        "lowpass": [25.0, 35.0, 40.0],
    },
    config=None,
):
    """Select corner frequencies.

    Note that this step only selects the highpass and lowpass corners. The results can
    be modifed by other steps (such as `lowpass_max_frequency`) and then the filters
    are applied with the `lowpass_filter` and `highpass_filter` steps.

    Args:
        st (gmprocess.core.stationstream.StationStream):
            Stream of data.
        event (gmprocess.utils.scalar_event.ScalarEvent):
            ScalarEvent object.
        method (str):
            Which method to use; currently allowed "snr" or "constant".
        constant(dict):
            Dictionary of `constant` method config options.
        snr (dict):
            Dictionary of `snr` method config options.
        magnitude (dict):
            Dictionary of `magnitude` method config options.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: Stream with selected corner frequencies added.
    """

    if method == "constant":
        st = from_constant(st, **constant)
    elif method == "magnitude":
        st = from_magnitude(st, event, **magnitude)
    elif method == "snr":
        st = from_snr(st, event, **snr)
        # Constrain the two horizontals to have the same corner frequencies?
        if snr["same_horiz"] and st.passed and st.num_horizontal > 1:
            hlps = [
                tr.get_parameter("corner_frequencies")["lowpass"]
                for tr in st if tr.is_horizontal
            ]
            hhps = [
                tr.get_parameter("corner_frequencies")["highpass"]
                for tr in st if tr.is_horizontal
            ]
            llp = np.min(hlps)
            hhp = np.max(hhps)
            for tr in st:
                if tr.is_horizontal:
                    cfdict = tr.get_parameter("corner_frequencies")
                    cfdict["lowpass"] = llp
                    cfdict["highpass"] = hhp
                    tr.set_parameter("corner_frequencies", cfdict)
    else:
        raise ValueError(
            "Corner frequency 'method' must be one of: 'constant', 'magnitude', or "
            "'snr'."
        )

    # Replace corners set in manual review
    for tr in st:
        if tr.has_parameter("review"):
            review_dict = tr.get_parameter("review")
            if "corner_frequencies" in review_dict:
                rev_fc_dict = review_dict["corner_frequencies"]
                if tr.has_parameter("corner_frequencies"):
                    base_fc_dict = tr.get_parameter("corner_frequencies")
                    base_fc_dict["type"] = "reviewed"
                else:
                    base_fc_dict = {"type": "reviewed"}
                if ("highpass" in rev_fc_dict) or ("lowpass" in rev_fc_dict):
                    if "highpass" in rev_fc_dict:
                        base_fc_dict["highpass"] = rev_fc_dict["highpass"]
                    if "lowpass" in rev_fc_dict:
                        base_fc_dict["lowpass"] = rev_fc_dict["lowpass"]
                    tr.set_parameter("corner_frequencies", base_fc_dict)
    return st


@processing_step
def lowpass_max_frequency(st, fn_fac=0.75, lp_max=40.0, config=None):
    """Cap lowpass corner frequency.

    Options on this include a constant maximum, or as a fraction of the Nyquist.

    Args:
        st (gmprocess.core.stationstream.StationStream):
            Stream of data.
        fn_fac (float):
            Factor to be multiplied by the Nyquist to cap the lowpass filter.
        lp_max (float):
            Maximum lowpass corner frequency (Hz).
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: Stream with lowpass frequency adjustment applied.
    """

    def _cap_lowpass(fc):
        freq_dict = tr.get_parameter("corner_frequencies")
        if freq_dict["lowpass"] > fc:
            freq_dict["lowpass"] = fc
            tr.set_parameter("corner_frequencies", freq_dict)

    for tr in st:
        if tr.passed:
            if tr.has_parameter("review"):
                rdict = tr.get_parameter("review")
                if "corner_frequencies" in rdict:
                    rev_fc_dict = rdict["corner_frequencies"]
                    if "lowpass" in rev_fc_dict:
                        logging.warning(
                            "Not applying lowpass_max_frequency for %s because the "
                            "lowpass filter corner was set by manual review.", tr
                        )
                        continue

            fn = 0.5 * tr.stats.sampling_rate
            lp_max_fn = fn * fn_fac
            _cap_lowpass(lp_max_fn)
            _cap_lowpass(lp_max)

    return st


def from_constant(st, highpass=0.08, lowpass=20.0):
    """Use constant corner frequencies across all records.

    Args:
        st (gmprocess.core.stationstream.StationStream):
            Stream of data.
        highpass (float):
            Highpass corner frequency (Hz).
        lowpass (float):
            Lowpass corner frequency (Hz).

    Returns:
        StationStream: Stream with selected corner frequencies appended to records.
    """
    for tr in st:
        tr.set_parameter(
            "corner_frequencies",
            {"type": "constant", "highpass": highpass, "lowpass": lowpass},
        )
    return st


def from_magnitude(
    st,
    event,
    minmag=[-999.0, 3.5, 5.5],
    highpass=[0.5, 0.3, 0.1],
    lowpass=[25.0, 35.0, 40.0],
):
    """Use constant corner frequencies across all records.

    Args:
        st (gmprocess.core.stationstream.StationStream):
            Stream of data.
        event (gmprocess.utils.scalar_event.ScalarEvent):
            ScalarEvent object.
        highpass (float):
            Highpass corner frequency (Hz).
        lowpass (float):
            Lowpass corner frequency (Hz).

    Returns:
        StationStream: Stream with selected corner frequencies appended to records.
    """
    mag = event.magnitude
    max_idx = np.max(np.where(mag > np.array(minmag))[0])
    hp_select = highpass[max_idx]
    lp_select = lowpass[max_idx]
    for tr in st:
        tr.set_parameter(
            "corner_frequencies",
            {"type": "magnitude", "highpass": hp_select, "lowpass": lp_select},
        )
    return st


def from_snr(st, event, same_horiz=True, smoothing_parameter=20):
    """Set corner frequencies from SNR.

    Args:
        st (StationStream):
            Stream of data.
        same_horiz (bool):
            If True, horizontal traces in the stream must have the same
            corner frequencies.
        smoothing_parameter (float):
            Konno-Omachi smoothing bandwidth parameter.

    Returns:
        StationStream: Stream with selected corner frequencies appended to records.
    """
    for tr in st:
        # Check for prior calculation of 'snr'
        if not tr.has_cached("snr"):
            tr = compute_snr_trace(tr, event.magnitude, smoothing_parameter)

        # If the SNR doesn't exist then it must have failed because it didn't
        # have enough points in the noise or signal windows
        if tr.passed:
            snr_conf = tr.get_parameter("snr_conf")
            threshold = snr_conf["threshold"]
            min_freq = snr_conf["min_freq"]
            max_freq = snr_conf["max_freq"]

            if tr.has_cached("snr"):
                snr_dict = tr.get_cached("snr")
            else:
                tr.fail(
                    "Cannot use SNR to pick corners because SNR could not "
                    "be calculated."
                )
                continue

            snr = snr_dict["snr"]
            freq = snr_dict["freq"]

            sign_diff = np.diff(np.sign(snr - threshold))
            np.nan_to_num(sign_diff, copy=False, nan=0.0, posinf=None, neginf=None)
            zero_crossings_idx = np.where(sign_diff != 0)[0]
            zero_crossing_grad = sign_diff[zero_crossings_idx]
            lows = freq[zero_crossings_idx[zero_crossing_grad > 0] + 1]
            highs = freq[zero_crossings_idx[zero_crossing_grad < 0]]
            if snr[~np.isnan(snr)][0] - threshold > 0:
                lows = np.insert(lows, 0, freq[0], axis=0)

            # If we didn't find any corners
            if len(lows) == 0:
                tr.fail("SNR not greater than required threshold.")
                continue

            # If we find an extra low, add another high for the maximum
            # frequency
            if len(lows) > len(highs):
                highs = np.append(highs, max(freq))

            # Check if any of the low/high pairs are valid
            found_valid = False
            for idx, val in enumerate(lows):
                if idx < len(highs):
                    if val <= min_freq and highs[idx] > max_freq:
                        low_corner = val
                        high_corner = highs[idx]
                        found_valid = True

            if found_valid:
                # Check to make sure that the highpass corner frequency is not
                # less than 1 / the duration of the waveform
                duration = (
                    tr.get_parameter("signal_end")["end_time"] - tr.stats.starttime
                )
                low_corner = max(1 / duration, low_corner)

                # Make sure highpass is greater than min freq of noise spectrum
                n_noise = len(tr.get_cached("preevent_noise_trace")["data"])
                min_freq_noise = 1.0 / n_noise / tr.stats.delta
                freq_hp = max(low_corner, min_freq_noise)

                tr.set_parameter(
                    "corner_frequencies",
                    {"type": "snr", "highpass": freq_hp, "lowpass": high_corner},
                )
            else:
                tr.fail("SNR not met within the required bandwidth.")
    return st
