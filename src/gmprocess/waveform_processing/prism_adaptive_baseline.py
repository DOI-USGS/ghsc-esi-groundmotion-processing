"""Module to implement the PRISM adaptive baseline correction processing step."""

import numpy as np
import statsmodels.formula.api as smf
import pandas as pd

from gmprocess.waveform_processing.processing_step import processing_step

RMSD_THRESHOLD = 6e-7


@processing_step
def prism_quality_criteria(
    st,
    lead_vel_threshold=0.1,
    trail_vel_threshold=0.1,
    trail_dis_threshold=0.1,
    config=None,
):
    """Apply the PRISM quality criteria.

    Based on the description in Jones et al. (2017; doi: 10.1785/0220160200).

    See discussion in the `prism_adaptive_baseline` docstring for the reasoning for
    why we have made this a separate processing step and how it relates to the
    adaptive baseline correction algorithm.

    Args:
        st (StationStream):
            Stream of data.
        lead_vel_threshold (float):
            Threshold for leading window velocity mean (cm/s).
        trail_vel_threshold (float):
            Threshold for trailing window velocity mean (cm/s).
        trail_dis_threshold (float):
            Threshold for trailing window displacement mean (cm/s).

    Returns:
        StationStream: Stream with the PRISM quality criteria applied.

    """
    if not st.passed:
        return st

    for tr in st:
        if tr.passed:
            tr_vel = tr.copy()
            tr_vel.integrate(**config["integration"])
            tr_dis = tr_vel.copy()
            tr_dis.integrate(**config["integration"])

            check_required_parameters(tr)
            split_time = tr.get_parameter("signal_split")["split_time"]
            event_onset = split_time - tr.stats.starttime
            lead_vel_qc = _quality_control(
                tr_vel,
                event_onset,
                "leading",
                lead_vel_threshold,
            )
            trail_vel_qc = _quality_control(
                tr_vel,
                event_onset,
                "trailing",
                trail_vel_threshold,
            )
            trail_dis_qc = _quality_control(
                tr_dis,
                event_onset,
                "trailing",
                trail_dis_threshold,
            )
            if not (lead_vel_qc and trail_vel_qc and trail_dis_qc):
                tr.fail("Failed PRISM quality criteria.")
    return st


@processing_step
def prism_adaptive_baseline(
    st,
    n_iter=100,
    lead_vel_threshold=0.1,
    trail_vel_threshold=0.1,
    config=None,
):
    """Apply the PRISM adaptive baseline correction step.

    Based on the description in Jones et al. (2017; doi: 10.1785/0220160200).

    Please note that the PRISM algorithm is presented as a full entire workflow and that
    the adaptive baseline correction step is difficult to separate into a singular step.
    More specifically, other processing steps that we treat as independent in gmprocess,
    like filtering and QA checks, are intertwined with the adaptive baseline correction
    (see Figs 2 and 5 in Jones et al., 2017).

    The first QA step (applied to the leading and tailing velocity window) is used to
    decide if the adaptive baseline correction is required. We include this QA step in
    this implementation because we do not want to apply the baseline correction
    unnecessarily. This first QA check is meant to be applied prior to any filtering.
    Thus, this processing step should not be configured to occur after filtering steps.
    If this QA step passes, then the input stream is not modified. If this QA step
    fails, then the record is modified using the adaptive baseline correction only,
    i.e., subtracting the derivative of the trend of the fit to velocity from the
    acceleration data. This last clarification is necessary because additional filtering
    is described as part of the adaptive baseline correction in Jones et al., and we
    prefer to have that occur as a separate processing step.

    The final QA step, which checks the mean velocity and displacement in the leading and
    trailing windows, is described to apply after bandpass filtering. Since we keep the
    filtering as a separate step, we also need to keep the final QA as a separate step.
    Thus, the stream is never failed failed by this adaptive baseline correction step.

    Args:
        st (StationStream):
            Stream of data.
        n_iter (int):
            Number of iterations to select time2.
        lead_vel_threshold (float):
            Threshold for leading window velocity mean (cm/s).
        trail_vel_threshold (float):
            Threshold for trailing window velocity mean (cm/s).
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: Stream with the adaptive baseline correction applied.
    """
    if not st.passed:
        return st

    for tr in st:
        if tr.passed:
            check_required_parameters(tr)
            split_time = tr.get_parameter("signal_split")["split_time"]
            event_onset = split_time - tr.stats.starttime
            noise = tr.copy().trim(endtime=split_time)
            noise_mean = np.mean(noise.data)
            velocity_bc = tr.copy()
            velocity_bc.data = velocity_bc.data - noise_mean
            # veloicty quality control
            lead_velocity_qc = _quality_control(
                velocity_bc,
                event_onset,
                "leading",
                lead_vel_threshold,
            )
            trail_velocity_qc = _quality_control(
                velocity_bc,
                event_onset,
                "trailing",
                trail_vel_threshold,
            )
            if lead_velocity_qc and trail_velocity_qc:
                # note: I want to put an entry in the provenance to document that the
                # trace was checked using this method and that it determined that no
                # baseline correction was necessary. this deviates from convention and
                # could be a mistake.
                tr.set_provenance(
                    "detrend",
                    {
                        "detrending_method": "PRISM adaptive baseline correction "
                        "passsed QA"
                    },
                )

            else:
                apply_prism_adaptive_baseline_correction(tr, n_iter, config)
                tr.set_provenance(
                    "detrend",
                    {"detrending_method": "PRISM adaptive baseline correction applied"},
                )
    return st


def apply_prism_adaptive_baseline_correction(
    trace,
    n_iter,
    config,
):
    """Function to apply PRISM adaptive baseline correction to a trace.

    Args:
        trace (StationTrace):
            Trace.
        n_iter (int):
            Number of iterations to select time2.
        config (dict):
            Config options.
    """
    trace_vel = trace.copy()
    trace_vel.integrate(**config["integration"])

    time1 = (
        trace_vel.get_parameter("signal_split")["split_time"]
        - trace_vel.stats.starttime
    )
    fhp = trace_vel.get_parameter("corner_frequencies")["highpass"]
    flc = fhp
    time2_min = time1 + 1 / flc

    # start with segment 1, it doesn't change with iterations
    segment1 = trace.copy()
    segment1.trim(endtime=segment1.stats.starttime + time1)

    s1fit = _find_best_fit_trend(segment1)

    # array of trial values for time2
    duration = trace_vel.stats.endtime - trace_vel.stats.starttime
    time2_max = duration - 1 / flc
    # TODO: should this time2_max be smaller?

    iteration_time2s = np.linspace(time2_min, time2_max, n_iter)

    # List to store results of each iteration
    iteration_list = []
    loss = []
    segment_fits = []
    for itime2 in iteration_time2s:
        segment2 = trace_vel.copy()
        segment2.trim(
            starttime=segment2.stats.starttime + time1,
            endtime=segment2.stats.starttime + itime2,
        )
        segment3 = trace_vel.copy()
        segment3.trim(starttime=segment3.stats.starttime + itime2)
        s3fit = _find_best_fit_trend(segment3)

        trend_trace = trace.copy()
        trend_trace.data = np.full_like(trend_trace.data, 1.0)

        t1end_idx = segment1.stats.npts
        trend_trace.data[:t1end_idx] = s1fit["trend"]
        t3start_idx = trend_trace.stats.npts - segment3.stats.npts
        trend_trace.data[t3start_idx:] = s3fit["trend"]

        prism_spline(trend_trace.data, t1end_idx - 1, t3start_idx, segment2.stats.delta)
        res_s1 = trace_vel.data[:t1end_idx]
        res_s2 = trace_vel.data[t1end_idx:t3start_idx]
        res_s3 = trace_vel.data[t3start_idx:]
        rmsd_s1 = np.sqrt(np.mean(res_s1**2))
        rmsd_s2 = np.sqrt(np.mean(res_s2**2))
        rmsd_s3 = np.sqrt(np.mean(res_s3**2))
        srss_rmsd = np.sqrt(np.sum(rmsd_s1**2 + rmsd_s2**2 + rmsd_s3**2))
        iteration_list.append(trend_trace)
        loss.append(srss_rmsd)
        segment_fits.append([s1fit, s3fit])

    ind_min_loss = np.argmin(loss)
    s1fit, s3fit = segment_fits[ind_min_loss]
    trend_trace = iteration_list[ind_min_loss]
    trend_deriv = trend_trace.copy()
    trend_deriv.differentiate()
    trend_deriv.data[: s1fit["npts"]] = s1fit["vel_fit_deriv"]
    t3start_idx = trend_deriv.stats.npts - s3fit["npts"]
    trend_deriv.data[t3start_idx:] = s3fit["vel_fit_deriv"]

    trace.data -= trend_deriv.data


def _quality_control(trace, event_onset, window_type, threshold):
    """Apply quality control criteria.

    Args:
        trace (Trace):
            Trace for quality control.
        event_onset (float):
            Event onset time from start of trace (sec).
        window_type (str):
            Which window to use? "leading" or "trailing."
        threshold (str):
            threshold for mean within window.

    Returns:
        bool: Does the trace pass quality control criteria?
    """
    if window_type not in ["leading", "trailing"]:
        raise ValueError("window must be either 'leading' or 'trailing'.")
    quality_control_pass = True

    fhp = trace.get_parameter("corner_frequencies")["highpass"]
    flc = fhp
    window_length = max(event_onset, 1 / flc)

    window = trace.copy()
    if window_type == "leading":
        # leading window is simple
        window_start = window.stats.starttime
        window_end = window.stats.starttime + window_length
    else:
        # trailing window involves zero crossings
        trailing_window = trace.copy()
        initial_start_time = trace.stats.endtime - window_length
        trailing_window.trim(starttime=initial_start_time)
        zarray = trailing_window[0:-1] * trailing_window[1:]

        # Check that there are zero crossings
        if len(zarray):
            zindices = [i for (i, z) in enumerate(zarray) if z < 0]
            # TODO: is there a mininum trailing window duration after zero-crossing
            #       criterial is applied?
            if len(zindices):
                window_start = trailing_window.times(type="utcdatetime")[zindices[0]]
            else:
                # NOTE: this is probably not correct.
                window_start = initial_start_time
        else:
            window_start = initial_start_time

        window_end = window.stats.endtime

    window.trim(starttime=window_start, endtime=window_end)
    window_mean = np.mean(window.data)

    if np.abs(window_mean) > threshold:
        quality_control_pass = False

    return quality_control_pass


def prism_spline(vals, break1, break2, intime):
    """Spline function for segment 2.

    Converted from PRISM function "getSplineSmooth" in
    prism_engine/src/SmProcessing/ABC2.java

    Args:
        vals (ndarray):
            input array of values, where the array between break1 and break2 will be
            filled with the calculated spline values
        break1 (int):
            location of last value of 1st baseline segment
        break2 (int):
            location of first value of 3rd baseline segment
        intime (float):
            time interval between samples.
    """
    t1 = break1 * intime
    t2 = break2 * intime
    loctime = np.linspace(0, intime * (len(vals) - 1), len(vals))
    time12 = intime * 12.0
    intlen = t2 - t1

    a = vals[break1]
    b = vals[break2]
    c = (
        3.0 * vals[break1 - 4]
        - 16.0 * vals[break1 - 3]
        + 36.0 * vals[break1 - 2]
        - 48.0 * vals[break1 - 1]
        + 25.0 * vals[break1]
    ) / time12
    d = (
        -25.0 * vals[break2]
        + 48.0 * vals[break2 + 1]
        - 36.0 * vals[break2 + 2]
        + 16.0 * vals[break2 + 3]
        - 3.0 * vals[break2 + 4]
    ) / time12

    for i in range(break1 + 1, break2):
        start = loctime[i] - t1
        end = loctime[i] - t2
        ssq = np.power(start, 2)
        esq = np.power(end, 2)
        vals[i] = (
            (1.0 + ((2.0 * start) / intlen)) * esq * a
            + (1.0 - ((2.0 * end) / intlen)) * ssq * b
            + start * esq * c
            + end * ssq * d
        )
        vals[i] = vals[i] / np.power(intlen, 2)


def _find_best_fit_trend(trace):
    # TODO: generalized this to allow for other polynomial orders
    times = trace.times()
    df = pd.DataFrame({"times": times, "times2": times**2, "data": trace.data})
    mod1 = smf.ols(formula="data ~ times", data=df)
    mod2 = smf.ols(formula="data ~ times + times2", data=df)
    res1 = mod1.fit()
    res2 = mod2.fit()
    pred1 = res1.predict()
    pred2 = res2.predict()

    rmsd1 = np.sqrt(np.mean((df["data"] - pred1) ** 2))
    rmsd2 = np.sqrt(np.mean((df["data"] - pred2) ** 2))

    # "select the model with lower rmsd" but order 2 will always win this
    # comparison. The Java implementation includes a threshold difference criterial
    # so that the linear model will be used if the difference is below a threshold:
    # if ((linrms < polrms)|| (Math.abs(linrms - polrms) < 5*Math.ulp(polrms))) {
    cond1 = rmsd1 < rmsd2
    cond2 = np.abs(rmsd1 - rmsd2) < RMSD_THRESHOLD
    if cond1 | cond2:
        vel_fit_params = np.array(res1.params)
    else:
        vel_fit_params = np.array(res2.params)

    # remove derivative of best-fit trend from acceleration
    if len(vel_fit_params) > 2:
        # Quadratic
        vel_fit_deriv = vel_fit_params[1] + 2 * times * vel_fit_params[2]
        trend = (
            vel_fit_params[0]
            + vel_fit_params[1] * times
            + vel_fit_params[2] * (times**2)
        )
    else:
        # Linear
        vel_fit_deriv = vel_fit_params[1]
        trend = vel_fit_params[0] + vel_fit_params[1] * times

    return {
        "vel_fit_deriv": vel_fit_deriv,
        "trend": trend,
        "npts": trace.stats.npts,
    }


def check_required_parameters(trace):
    if not trace.has_parameter("signal_split"):
        raise ValueError("Split time not set, run 'signal_split'.")
    if not trace.has_parameter("corner_frequencies"):
        raise ValueError("Corner frequencies not set, run 'get_corner_frequencies'.")
