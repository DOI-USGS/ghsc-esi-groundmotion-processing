"""Module for signal-to-noise-ratio calculations."""

import numpy as np
from obspy.signal.util import next_pow_2

from gmprocess.waveform_processing.fft import compute_and_smooth_spectrum
from gmprocess.waveform_processing.spectrum import brune_f0, moment_from_magnitude
from gmprocess.waveform_processing.processing_step import processing_step
from gmprocess.waveform_processing.windows import duration_from_magnitude


# Options for tapering noise/signal windows
TAPER_WIDTH = 0.05
TAPER_TYPE = "hann"
TAPER_SIDE = "both"
MIN_POINTS_IN_WINDOW = 10


@processing_step
def compute_snr(st, event, smoothing_parameter=20.0, config=None):
    """Compute SNR dictionaries for a stream, looping over all traces.

    Args:
        st (StationStream):
           Trace of data.
        event (ScalarEvent):
           ScalarEvent object.
        smoothing_parameter (float):
           Konno-Omachi smoothing bandwidth parameter.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: With SNR dictionaries added as trace parameters.
    """
    for tr in st:
        # Require that units are accel
        if tr.stats.standard.units_type != "acc":
            tr.fail("Unit type must be acc to compute SNR.")
            continue

        # Do we have estimates of the signal split time?
        compute_snr_trace(tr, event.magnitude, smoothing_parameter)
    return st


@processing_step
def snr_check(
    st,
    mag,
    threshold=2.0,
    min_freq="f0",
    max_freq=5.0,
    f0_options={"stress_drop": 10, "shear_vel": 3.7, "ceiling": 2.0, "floor": 0.1},
    config=None,
):
    """Check signal-to-noise ratio.

    Requires noise/signal windowing to have succeeded.

    Args:
        st (StationStream):
           Trace of data.
        mag (float):
            Earthquake magnitude.
        threshold (float):
            Threshold SNR value.
        min_freq (float or str):
            Minimum frequency for threshold to be exeeded. If 'f0', then the
            Brune corner frequency will be used.
        max_freq (float):
            Maximum frequency for threshold to be exeeded.
        smoothing_parameter (float):
            Konno-Omachi smoothing bandwidth parameter.
        f0_options (dict):
            Dictionary of f0 options (see config file).
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        trace: Trace with SNR check.
    """
    for tr in st:
        if tr.has_cached("snr"):
            snr_dict = tr.get_cached("snr")
            snr = np.array(snr_dict["snr"])
            freq = np.array(snr_dict["freq"])

            # If min_freq is 'f0', then compute Brune corner frequency
            if min_freq == "f0":
                min_freq = brune_f0(
                    moment_from_magnitude(mag),
                    f0_options["stress_drop"],
                    f0_options["shear_vel"],
                )
                if min_freq < f0_options["floor"]:
                    min_freq = f0_options["floor"]
                if min_freq > f0_options["ceiling"]:
                    min_freq = f0_options["ceiling"]

            # Check if signal criteria is met
            mask = (freq >= min_freq) & (freq <= max_freq)
            if np.any(mask):
                min_snr = np.min(snr[mask])
            else:
                min_snr = 0

            if min_snr < threshold:
                tr.fail("Failed SNR check.")
        snr_conf = {"threshold": threshold, "min_freq": min_freq, "max_freq": max_freq}
        tr.set_parameter("snr_conf", snr_conf)
    return st


def compute_snr_trace(tr, event_magnitude, smoothing_parameter=20.0):
    """Compute SNR dictionaries for a trace.

    Args:
        event_magnitude (float):
            Earthquake magnitude.
        smoothing_parameter (float):
            Konno-Omachi smoothing bandwidth parameter.

    """

    def _compute_event_spectra(
        preevent_noise_spectrum, event_spectrum, dur_preevent, dur_event
    ):
        """Compute noise and signal spectra from event spectrum using pre-event noise spectrum
        to estimate the event noise spectrum.

        Assumptions:
          - Noise amplitudes scale as sqrt(duration)
          - Noise is stationary and so duration is the length of the prevent window (prevent_noise) and
            and event window (event noise).

        event_spectrum = event_noise_spectrum + event_signal_spectrum

        Noise is stationary => noise spectra normalized by duration are equal ->
        pre-event noise spectrum / sqrt(pre-event duration) = event noise spectra / sqrt(event duration)
        """
        event_noise_spectrum = (
            preevent_noise_spectrum * np.sqrt(dur_event) / np.sqrt(dur_preevent)
        )
        signal_spectrum = event_spectrum - event_noise_spectrum
        return (event_noise_spectrum, signal_spectrum)

    if tr.has_parameter("signal_split"):
        # Split the noise and signal into two separate traces
        split_prov = tr.get_parameter("signal_split")
        if isinstance(split_prov, list):
            split_prov = split_prov[0]
        split_time = split_prov["split_time"]
        preevent_noise = tr.copy().trim(endtime=split_time)
        event = tr.copy().trim(starttime=split_time)

        tr.set_cached(
            "preevent_noise_trace",
            {"times": preevent_noise.times(), "data": preevent_noise.data},
        )

        # Need to ensure consistency of the assumed duration for normalizing the SNR
        # with the actual windowed duration of the event window.
        dur_shaking = duration_from_magnitude(event_magnitude)
        tr.set_parameter("signal_spectrum", {"duration": dur_shaking})
        dur_event = event.stats.endtime - event.stats.starttime
        if dur_shaking < dur_event:
            event.trim(endtime=event.stats.starttime + dur_shaking)
            dur_event = dur_shaking
        else:
            dur_shaking = dur_event

        # Detrend
        preevent_noise.detrend("demean")
        event.detrend("demean")

        # Taper both windows
        preevent_noise.taper(
            max_percentage=TAPER_WIDTH, type=TAPER_TYPE, side=TAPER_SIDE
        )
        event.taper(max_percentage=TAPER_WIDTH, type=TAPER_TYPE, side=TAPER_SIDE)

        # Check that there are a minimum number of points in the noise window
        if preevent_noise.stats.npts < MIN_POINTS_IN_WINDOW:
            # Fail the trace, but still compute the event spectra
            # ** only fail here if it hasn't already failed; we do not yet
            # ** support tracking multiple fail reasons and I think it is
            # ** better to know the FIRST reason if I have to pick one.
            if tr.passed:
                tr.fail("SNR check; Not enough points in noise window")
            compute_and_smooth_spectrum(tr, smoothing_parameter, "event")
            return tr

        # Check that there are a minimum number of points in the event window
        if event.stats.npts < MIN_POINTS_IN_WINDOW:
            # Fail the trace, but still compute the event spectra
            if tr.passed:
                tr.fail("SNR check; Not enough points in event window")
            compute_and_smooth_spectrum(tr, smoothing_parameter, "event")
            return tr

        nfft = max(
            next_pow_2(event.stats.npts),
            next_pow_2(preevent_noise.stats.npts),
        )

        compute_and_smooth_spectrum(
            tr, smoothing_parameter, "noise", preevent_noise, nfft=nfft
        )
        compute_and_smooth_spectrum(tr, smoothing_parameter, "event", event, nfft=nfft)

        # Noise, event, and signal durations.
        #
        # - Pre-event noise duration is the pre-event window duration.
        # - Event noise duration is the event window duration.
        # - Ground motions at these frequencies are approximately white noise, and thus
        #   also scale as sqrt(duration); ground motion is not stationary, so we'll use
        #   the duration estimated from the earthquake magnitude.
        dur_preevent = preevent_noise.stats.endtime - preevent_noise.stats.starttime

        # Compute noise and signal spectra.
        preevent_noise_spectrum = tr.get_cached("noise_spectrum")["spec"]
        event_spectrum = tr.get_cached("event_spectrum")["spec"]
        event_noise_spectrum, signal_spectrum = _compute_event_spectra(
            preevent_noise_spectrum, event_spectrum, dur_preevent, dur_event
        )
        tr.set_cached(
            "noise_spectrum",
            {
                "spec": event_noise_spectrum,
                "freq": tr.get_cached("noise_spectrum")["freq"],
            },
        )
        tr.set_parameter("noise_spectrum", {"duration": dur_preevent})
        tr.set_cached(
            "signal_spectrum",
            {
                "spec": signal_spectrum,
                "freq": tr.get_cached("event_spectrum")["freq"],
            },
        )

        # Compute smooth noise and signal.
        smooth_preevent_noise_spectrum = tr.get_cached("smooth_noise_spectrum")["spec"]
        smooth_event_spectrum = tr.get_cached("smooth_event_spectrum")["spec"]
        smooth_event_noise_spectrum, smooth_signal_spectrum = _compute_event_spectra(
            smooth_preevent_noise_spectrum,
            smooth_event_spectrum,
            dur_preevent,
            dur_event,
        )
        tr.set_cached(
            "smooth_noise_spectrum",
            {
                "spec": smooth_event_noise_spectrum,
                "freq": tr.get_cached("smooth_noise_spectrum")["freq"],
            },
        )
        tr.set_cached(
            "smooth_signal_spectrum",
            {
                "spec": smooth_signal_spectrum,
                "freq": tr.get_cached("smooth_event_spectrum")["freq"],
            },
        )

        smooth_event_noise_normspectrum = smooth_event_noise_spectrum / np.sqrt(
            dur_preevent
        )
        smooth_signal_normspectrum = smooth_signal_spectrum / np.sqrt(dur_shaking)
        snr = smooth_signal_normspectrum / smooth_event_noise_normspectrum
        tr.set_cached(
            "snr",
            {
                "snr": snr,
                "freq": tr.get_cached("smooth_event_spectrum")["freq"],
            },
        )

    else:
        # We do not have an estimate of the event split time for this trace
        compute_and_smooth_spectrum(tr, smoothing_parameter, "event")

    return tr
