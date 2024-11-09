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
from gmprocess.metrics.waveform_metric_collection import WaveformMetricCollection
from gmprocess.utils.ground_motion_models import load_model
from gmprocess.waveform_processing.processing_step import processing_step

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
def cut(st, sec_before_split=2.0, config=None):
    """Cut/trim the record.

    This method minimally requires that the windows.signal_end method has been
    run, in which case the record is trimmed to the end of the signal that
    was estimated by that method.

    To trim the beginning of the record, the sec_before_split must be
    specified, which uses the noise/signal split time that was estiamted by the
    windows.signal_split mehtod.

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
        logging.debug(f"Before cut end time: {tr.stats.endtime}")
        etime = tr.get_parameter("signal_end")["end_time"]
        tr.trim(endtime=etime)
        logging.debug(f"After cut end time: {tr.stats.endtime}")
        if sec_before_split is not None:
            split_time = tr.get_parameter("signal_split")["split_time"]
            stime = split_time - sec_before_split
            logging.debug(f"Before cut start time: {tr.stats.starttime}")
            if stime < etime:
                tr.trim(starttime=stime)
            else:
                tr.fail(
                    "The 'cut' processing step resulting in incompatible start "
                    "and end times."
                )
            logging.debug(f"After cut start time: {tr.stats.starttime}")
        tr.set_provenance(
            "cut",
            {
                "new_start_time": tr.stats.starttime,
                "new_end_time": tr.stats.endtime,
            },
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


def signal_split(st, event, model=None, config=None):
    """
    This method tries to identifies the boundary between the noise and signal
    for the waveform. The split time is placed inside the
    'processing_parameters' key of the trace stats.

    The P-wave arrival is used as the split between the noise and signal
    windows. Multiple picker methods are suppored and can be configured in the
    config file
    '~/.gmprocess/picker.yml

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
    if loc > 0:
        tsplit = st[0].stats.starttime + loc
        preferred_picker = "travel_time"
    else:
        pick_methods = ["ar", "baer", "power", "kalkan"]
        rows = []
        for pick_method in pick_methods:
            try:
                if pick_method == "ar":
                    loc, mean_snr = pick_ar(st, config=config)
                elif pick_method == "baer":
                    loc, mean_snr = pick_baer(st, config=config)
                elif pick_method == "power":
                    loc, mean_snr = pick_power(st, config=config)
                elif pick_method == "kalkan":
                    loc, mean_snr = pick_kalkan(st, config=config)
                elif pick_method == "yeck":
                    loc, mean_snr = pick_yeck(st, config=config)
            except BaseException:
                loc = -1
                mean_snr = np.nan
            rows.append(
                {
                    "Stream": st.get_id(),
                    "Method": pick_method,
                    "Pick_Time": loc,
                    "Mean_SNR": mean_snr,
                }
            )
        df = pd.DataFrame(rows)

        max_snr = df["Mean_SNR"].max()
        if not np.isnan(max_snr):
            maxrow = df[df["Mean_SNR"] == max_snr].iloc[0]
            tsplit = st[0].stats.starttime + maxrow["Pick_Time"]
            preferred_picker = maxrow["Method"]
        else:
            tsplit = -1

    # the user may have specified a p_arrival_shift value.
    # this is used to shift the P arrival time (i.e., the break between the
    # noise and signal windows).
    shift = 0.0
    if "p_arrival_shift" in picker_config:
        shift = picker_config["p_arrival_shift"]
        if tsplit + shift >= st[0].stats.starttime:
            tsplit += shift

    if tsplit >= st[0].stats.starttime:
        # Update trace params
        split_params = {
            "split_time": tsplit,
            "method": "p_arrival",
            "picker_type": preferred_picker,
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
    vmin=1.0,
    floor=120.0,
    model="AS16",
    epsilon=3.0,
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
        vmin (float):
            Velocity (km/s) for estimating end of signal. Only used if
            method="velocity".
        floor (float):
            Minimum duration (sec) applied along with vmin.
        model (str):
            Short name of duration model to use. Must be defined in the
            gmprocess/data/modules.yml file.
        epsilon (float):
            Number of standard deviations; if epsilon is 1.0, then the signal
            window duration is the mean Ds + 1 standard deviation. Only used
            for method="model".

    Returns:
        trace with stats dict updated to include a
        stats['processing_parameters']['signal_end'] dictionary.

    """
    for tr in st:
        if not tr.has_parameter("signal_split"):
            logging.warning("No signal split in trace, cannot set signal end.")
            continue
        if method == "velocity":
            if vmin is None:
                raise ValueError('Must specify vmin if method is "velocity".')
            if floor is None:
                raise ValueError('Must specify floor if method is "velocity".')
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

            # Get split time
            split_time = tr.get_parameter("signal_split")["split_time"]
            end_time = split_time + float(duration)
        elif method == "magnitude":
            end_time = event_time + duration_from_magnitude(event_mag)
        elif method == "none":
            # need defaults
            end_time = tr.stats.endtime
        else:
            raise ValueError(
                'method must be one of: "velocity", "model", "magnitude", or "none".'
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
