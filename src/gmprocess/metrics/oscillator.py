"""Module for computing oscillator response for a trace."""

from esi_core.gmprocess.metrics.oscillators import calculate_spectrals as spec_calc


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
        # leaving this out for now; it slows things down but doesn't
        # appear to affect the results. YMMV.
        # new_np = 1 if new_np == 0 else 2**(new_np - 1).bit_length()
        # The new sample interval
        new_dt = tlen / (new_np - 1)
        # The new sample rate
        new_sample_rate = 1.0 / new_dt
        # Make a copy because resampling happens in place
        trace = trace.copy()
        # Resample the trace
        trace.resample(new_sample_rate)

    sa_list = spec_calc(trace.data, new_np, new_dt, new_sample_rate, period, damping)
    return sa_list
