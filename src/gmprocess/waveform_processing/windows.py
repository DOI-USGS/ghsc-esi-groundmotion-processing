"""Helper functions for windowing singal and noise in a trace."""

import logging

import numpy as np
import pandas as pd

from openquake.hazardlib.contexts import simple_cmaker

from obspy.geodetics.base import gps2dist_azimuth

from gmprocess.waveform_processing.phase import (
    pick_power,
    pick_ar,
    pick_baer,
    pick_yeck,
    pick_kalkan,
    pick_travel,
)
from gmprocess.utils.config import get_config
from gmprocess.utils.ground_motion_models import load_model
from gmprocess.waveform_processing.processing_step import processing_step
from gmprocess.waveform_processing.spectrum import brune_f0, moment_from_magnitude

M_TO_KM = 1.0 / 1000


def duration_from_magnitude(event_magnitude):
    """Compute shaking duration in seconds from earthquake magnitude.

    From Hamid Haddadi, generic ground-motion record duration, (including 30s pre-event
    window: Duration (minutes) = earthquake magnitude / 2.0 .

    Args:
        event_magnitude (float):
            Earthquake magnitude.
    Returns:
        Duration of earthquake shaking in seconds.
    """
    return event_magnitude / 2.0 * 60.0 - 30.0


@processing_step
def cut(st, sec_before_split=30.0, config=None):
    """Cut/trim the record.

    This method minimally requires that the windows.signal_end method has been
    run, in which case the record is trimmed to the end of the signal that
    was estimated by that method.

    To trim the beginning of the record, the sec_before_split must be
    specified, which uses the noise/signal split time that was estimated by the
    windows.signal_split method.

    Args:
        st (StationStream):
            Stream of data.
        sec_before_split (float):
            Seconds to trim before split. If None, then the beginning of the
            record will be unchanged.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: With the cut applied.
    """
    if not st.passed:
        return st

    for tr in st:
        # Note that for consistency, we should clip all stream traces to the same
        # window and so, unlike other similar processing step loops, there should NOT
        # be an `if tr.passed` here.
        etime = tr.get_parameter("signal_end")["end_time"]
        tr.trim(endtime=etime)
        if sec_before_split is not None:
            split_time = tr.get_parameter("signal_split")["split_time"]
            stime = split_time - sec_before_split
            if stime < etime:
                tr.trim(starttime=stime)
            else:
                tr.fail(
                    "The 'cut' processing step resulted in incompatible start "
                    "and end times."
                )

    return st


def window_checks(st, min_noise_duration=0.5, min_signal_duration=5.0):
    """
    Check if the split/end windowing have long enough durations.

    Args:
        st (StationStream):
            Stream of data.

        min_noise_duration (float):
            Minimum duration of noise window (sec).
        min_signal_duration (float):
            Minimum duration of signal window (sec).


    """
    for tr in st:
        if tr.passed:
            if not tr.has_parameter("signal_split"):
                if tr.passed:
                    tr.fail("Cannot check window because no split time available.")
                continue
            # Split the noise and signal into two separate traces
            split_prov = tr.get_parameter("signal_split")
            if isinstance(split_prov, list):
                split_prov = split_prov[0]
            split_time = split_prov["split_time"]
            noise_duration = split_time - tr.stats.starttime
            signal_duration = tr.stats.endtime - split_time
            if noise_duration < min_noise_duration:
                tr.fail("Failed noise window duration check.")
            if signal_duration < min_signal_duration:
                tr.fail("Failed signal window duration check.")

    return st


def plot_pick(stream, event, utc_pick):
    from matplotlib import pyplot

    figure = pyplot.figure(figsize=(8.5, 9.0), layout="constrained")
    grid = figure.add_gridspec(3, 2)

    t_pick = utc_pick - stream[0].stats.starttime
    t_split = t_pick - 1.0
    for i_comp, trace in enumerate(stream):
        ax = figure.add_subplot(grid[i_comp, 0])
        ax.plot(trace.times(), trace.data, lw=0.5)
        ax.axvline(t_pick, color="red", ls="dashed")
        ax.axvline(t_split, color="green", ls="dashed")
        ax.set_xlim(t_pick-10, t_pick+10)

        ax = figure.add_subplot(grid[i_comp, 1])
        ax.plot(trace.times(), trace.data, lw=0.5)
        ax.axvline(t_pick, color="red", ls="dashed")
        ax.axvline(t_split, color="green", ls="dashed")
    filename = f"pick_{event.id}_{stream.get_id()}.png"
    pyplot.savefig(filename)
    pyplot.close(figure)


def signal_split(st, event, model=None, config=None):
    """
    This method tries to identifies the boundary between the noise and signal
    for the waveform. The split time is placed inside the
    'processing_parameters' key of the trace stats.

    The P-phase arrival is used as the split between the noise and signal
    windows. The default behavior uses the median value of the P-phase arrival
    from multiple methods within a 10s window of the expected travel time.

    Args:
        st (StationStream):
            Stream of data.
        event (ScalarEvent):
            ScalarEvent object.
        model (TauPyModel):
            TauPyModel object for computing travel times.
        config (dict):
            Dictionary containing system configuration information.

    Returns:
        trace with stats dict updated to include a
        stats['processing_parameters']['signal_split'] dictionary.
    """
    if config is None:
        config = get_config()

    # If we are in "no noise" window mode, then set the split time to the start time
    if config["windows"]["no_noise"]:
        tsplit = st[0].stats.starttime
        split_params = {
            "split_time": tsplit,
            "method": "no noise window",
            "picker_type": "none",
        }
        for tr in st:
            tr.set_parameter("signal_split", split_params)
        return st

    picker_config = config["pickers"]

    loc, mean_snr = pick_travel(st, event, config, model)
    pick_methods = picker_config["methods"]
    if loc > 0 and len(pick_methods) == 1 and pick_methods[0] == "travel_time":
        st_tsplit = st[0].stats.starttime + loc
        st_picker = "travel_time"
    else:
        pick_methods = picker_config["methods"]
        pick_window = picker_config.get("window", 10.0)
        pick_combine = picker_config.get("combine", "median")
        p_arrival = st[0].stats.starttime + loc
        st_windowed = st.copy().trim(starttime=p_arrival-pick_window, endtime=p_arrival+pick_window)

        pickers = {
            "travel_time": {
                "fn": pick_travel,
                "args": {
                    "event": event,
                    "config": config,
                    "model": model,
                },
            },
            "ar": {
                "fn": pick_ar,
                "args": {
                    "config": config,
                },
            },
            "baer": {
                "fn": pick_baer,
                "args": {
                    "config": config,
                },
            },
            "power": {
                "fn": pick_power,
                "args": {
                    "config": config,
                },
            },
            "kalkan": {
                "fn": pick_kalkan,
                "args": {
                    "config": config,
                },
            },
            "yeck": {
                "fn": pick_yeck,
                "args": {
                    "config": config,
                },
            },
        }
        picks_time = []
        picks_snr = []
        for pick_method in pick_methods:
            try:
                pick_info = pickers[pick_method]
                loc, mean_snr = pick_info["fn"](st_windowed, **pick_info["args"])
                if loc < 0:
                    loc = np.nan
            except BaseException:
                loc = np.nan
                mean_snr = np.nan
            picks_time.append(loc)
            picks_snr.append(mean_snr)
        picks_time = np.array(picks_time)

        # Combine picks
        if np.all(np.isnan(picks_time)):
            st_tsplit = st[0].stats.starttime
            st_picker = "None"
        elif pick_combine == "median":
            st_tsplit = st_windowed[0].stats.starttime + np.nanmedian(picks_time)
            st_picker = f"median({', '.join(pick_methods)})"
        elif pick_combine == "mean":
            st_tsplit = st_windowed[0].stats.starttime + np.nanmean(picks_time)
            st_picker = f"mean({', '.join(pick_methods)})"
        elif pick_combine == "max_snr":
            i_picker = np.nanargmax(picks_snr)
            st_tsplit = st_windowed[0].stats.starttime + picks_time[i_picker]
            st_picker = pick_methods[i_picker]
        else:
            raise ValueError(f"Unknown method {pick_combine} for combining picks.")

        diff_warning = picker_config.get("pick_travel_time_warning", 3.0)
        if abs(p_arrival - st_tsplit) > diff_warning:
            logging.warning(f"P wave pick differs from travel time by {st_tsplit-p_arrival:.2f}s for {event.id} at {st.get_id()}")

    if picker_config.get("plot_picks", False):
        plot_pick(st, event, st_tsplit)

    # The user may have specified a p_arrival_shift value.
    # this is used to shift the P arrival time (i.e., the break between the
    # noise and signal windows).
    shift = picker_config.get("p_arrival_shift", 0.0)
    st_tsplit = max(st[0].stats.starttime, st_tsplit + shift)

    if st_tsplit >= st[0].stats.starttime:
        # Update trace params
        split_params = {
            "split_time": st_tsplit,
            "method": "p_arrival",
            "picker_type": st_picker,
        }
        for tr in st:
            tr.set_parameter("signal_split", split_params)

    return st


def signal_end(
    st,
    event_time,
    event_lon,
    event_lat,
    event_mag,
    method="model",
    model="AS16",
    epsilon=3.0,
    stress_drop=10.0,
    dur0=150.0,
    dur1=0.6,
    vmin=1.0,
    floor=120.0,
):
    """
    Estimate end of signal by using a model of the 5-95% significant
    duration, and adding this value to the "signal_split" time. This probably
    only works well when the split is estimated with a p-wave picker since
    the velocity method often ends up with split times that are well before
    signal actually starts.

    Args:
        st (StationStream):
            Stream of data.
        event_time (UTCDateTime):
            Event origin time.
        event_mag (float):
            Event magnitude.
        event_lon (float):
            Event longitude.
        event_lat (float):
            Event latitude.
        method (str):
            Method for estimating signal end time. Can be 'velocity', 'model',
            'magnitude', or 'none'.
        model (str):
            Short name of duration model to use. Must be defined in the
            gmprocess/data/modules.yml file. Used with "model" method.
        epsilon (float):
            Number of standard deviations; if epsilon is 1.0, then the signal
            window duration is the mean Ds + 1 standard deviation. Only used
            for method="model". Used with "model" method.
        stress_drop (float):
            Stress drop (bars) for estimating source duration. Used with "source_path"
            method.
        dur0 (float):
            Path duration at zero distance (sec). Used with "source_path" method.
        dur1 (float):
            Path duration coefficient for distance term. Used with "source_path" method.
        vmin (float):
            Velocity (km/s) for estimating end of signal. Only used if
            method="velocity". Used with "velocity" method.
        floor (float):
            Minimum duration (sec) applied along with vmin. Used with "velocity" method.

    Returns:
        trace with stats dict updated to include a
        stats['processing_parameters']['signal_end'] dictionary.

    """
    for tr in st:
        if not tr.has_parameter("signal_split"):
            logging.warning("No signal split in trace, cannot set signal end.")
            continue
        # Get split time
        split_time = tr.get_parameter("signal_split")["split_time"]
        if method == "velocity":
            epi_dist = (
                gps2dist_azimuth(
                    lat1=event_lat,
                    lon1=event_lon,
                    lat2=tr.stats["coordinates"]["latitude"],
                    lon2=tr.stats["coordinates"]["longitude"],
                )[0]
                / 1000.0
            )
            end_time = event_time + max(floor, epi_dist / vmin)
        elif method == "source_path":
            moment = moment_from_magnitude(event_mag)
            fc = brune_f0(moment, stress_drop)
            source_duration = 1 / fc
            epi_dist = (
                gps2dist_azimuth(
                    lat1=event_lat,
                    lon1=event_lon,
                    lat2=tr.stats["coordinates"]["latitude"],
                    lon2=tr.stats["coordinates"]["longitude"],
                )[0]
                / 1000.0
            )
            end_time = split_time + source_duration + dur0 + dur1 * epi_dist
        elif method == "model":
            if model is None:
                raise ValueError('Must specify model if method is "model".')
            dmodel = load_model(model)

            # Set some "conservative" inputs (in that they will tend to give
            # larger durations).
            cmaker = simple_cmaker([dmodel], ["RSD595"], mags="%2.f" % event_mag)
            ctx = cmaker.new_ctx(1)
            ctx["mag"] = event_mag
            ctx["rake"] = -90.0
            ctx["vs30"] = np.array([180.0])
            ctx["z1pt0"] = np.array([0.51])
            epi_dist = (
                gps2dist_azimuth(
                    lat1=event_lat,
                    lon1=event_lon,
                    lat2=tr.stats["coordinates"]["latitude"],
                    lon2=tr.stats["coordinates"]["longitude"],
                )[0]
                / 1000.0
            )
            # Repi >= Rrup, so substitution here should be conservative
            # (leading to larger durations).
            ctx["rrup"] = np.array([epi_dist])

            result = cmaker.get_mean_stds([ctx])
            lnmu = result[0][0][0]
            lnstd = result[1][0][0]

            duration = np.exp(lnmu + epsilon * lnstd)

            end_time = split_time + float(duration)
        elif method == "magnitude":
            end_time = event_time + duration_from_magnitude(event_mag)
        elif method == "none":
            # need defaults
            end_time = tr.stats.endtime
        else:
            raise ValueError(
                'method must be one of: "source_path", "velocity", "model", '
                '"magnitude", or "none".'
            )
        # Update trace params
        end_params = {
            "end_time": end_time,
            "method": method,
            "vsplit": vmin,
            "floor": floor,
            "model": model,
            "epsilon": epsilon,
        }
        tr.set_parameter("signal_end", end_params)

    return st
