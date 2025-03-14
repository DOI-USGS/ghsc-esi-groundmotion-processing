"""Module for computing oscillator response for a trace."""

import numpy as np
from scipy.signal import windows

from esi_core.gmprocess.metrics import oscillators


def get_window(npts, percent=0.02):
    half_width = int(0.5 * percent * npts)
    taper = windows.hann(2 * half_width)
    window = np.ones((npts,))
    window[:half_width] = taper[:half_width]
    window[(npts - half_width) :] = taper[half_width:]
    return np.fft.ifftshift(window)


def calculate_spectrals(trace, period, damping):
    """
    Pull some stuff out of cython that shouldn't be there.
    """
    new_dt = trace.stats.delta
    new_np = trace.stats.npts
    new_sample_rate = trace.stats.sampling_rate
    tlen = (new_np - 1) * new_dt
    # This is the resample factor for low-sample-rate/high-frequency
    ns = (int)(10.0 * new_dt / period - 0.01) + 1
    if ns > 1:
        # Increase the number of samples as necessary
        new_np = new_np * ns
        # Make the new number of samples a power of two
        new_np = 1 if new_np == 0 else 2 ** (new_np - 1).bit_length()
        # The new sample interval
        new_dt = tlen / (new_np - 1)
        # The new sample rate
        new_sample_rate = 1.0 / new_dt
        # Make a copy because resampling happens in place
        trace = trace.copy()
        # Resample the trace
        window = get_window(trace.stats.npts, percent=0.02)
        trace.resample(new_sample_rate, window=window)
    sa_list = oscillators.calculate_spectrals(trace.data, new_np, new_dt, new_sample_rate, period, damping)
    # Note: sa_list has elements: [total acc, relative vel, relative dis], in which
    #       each element is an ndarray.
    return sa_list
