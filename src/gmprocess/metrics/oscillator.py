"""Module for computing oscillator response for a trace."""

import matplotlib.pyplot as plt

from esi_core.gmprocess.metrics.oscillators import calculate_spectrals as spec_calc


def calculate_spectrals(trace, period, damping):
    """
    Pull some stuff out of cython that shouldn't be there.
    """
    pfile1 = "/Users/emthompson/scratch/resample_test1.png"
    pfile1 = "/Users/emthompson/scratch/resample_test2.png"
    # trace.taper()
    ttimes = trace.times()
    trace.taper(max_percentage=0.05)
    plt.plot(ttimes, trace.data, "-")
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
        trace.resample(new_sample_rate, window=None)
        # "lanczos" method is about 10x slower
        # trace.interpolate(new_sample_rate, method="lanczos", a=10)
    ttimes2 = trace.times()
    plt.plot(ttimes2, trace.data, "-")
    # plt.xlim(0, 20)
    plt.savefig(pfile1, dpi=300)
    plt.close()

    sa_list = spec_calc(trace.data, new_np, new_dt, new_sample_rate, period, damping)
    return sa_list
