#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Module for miscenaleous convenience plotting functions not used by summary plots.
"""

import copy
import datetime
from collections import Counter

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from obspy.geodetics.base import gps2dist_azimuth
from esi_utils_colors.cpalette import ColorPalette
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.dates import num2date

from gmprocess.metrics.transform.oscillator import get_spectral

MIN_MAG = 4.0
MAX_MAG = 7.0
DELTA_MAG = 0.5

BOTTOM = 0.1
AX1_LEFT = 0.1
AX1_WIDTH = 0.8
AX1_HEIGHT = 0.8
AX2_WIDTH = 0.1
AX2_HEIGHT = 1.0

# avoid this issue: https://github.com/matplotlib/matplotlib/issues/5907
plt.rcParams["agg.path.chunksize"] = 10000


def plot_regression(
    event_table,
    imc,
    imc_table,
    imt,
    filename,
    distance_metric="EpicentralDistance",
    colormap="viridis",
):
    """Make summary "regression" plot.

    TODO:
      * Add GMPE curve and compute mean/sd for all the observations
        and then also report the standardized residuals.
      * Better definitions of column names and units.

    """
    fig = plt.figure(figsize=(10, 5))
    ax = fig.add_axes([BOTTOM, AX1_LEFT, AX1_WIDTH, AX1_HEIGHT])

    if distance_metric not in imc_table.columns:
        raise KeyError(f'Distance metric "{distance_metric}" not found in table')
    imt = imt.upper()

    # Stupid hack to get units for now. Need a better, more systematic
    # approach
    if imt.startswith("SA") | (imt == "PGA"):
        units = "%g"
    elif imt.startswith("FAS") or imt in ["ARIAS", "PGV"]:
        units = "cm/s"
    else:
        units = f"Unknown units for IMT {imt}"

    if imt not in imc_table.columns:
        raise KeyError(f'IMT "{imt}" not found in table')
    # get the event information
    # group imt data by event id
    # plot imts by event using colors banded by magnitude
    eventids = event_table["id"]
    # set up the color bands
    minmag = event_table["magnitude"].min()
    min_mag = min(np.floor(minmag / DELTA_MAG) * DELTA_MAG, MIN_MAG)
    maxmag = event_table["magnitude"].max()
    max_mag = max(np.ceil(maxmag / DELTA_MAG) * DELTA_MAG, MAX_MAG)
    z0 = np.arange(min_mag, max_mag, 0.5)
    z1 = np.arange(min_mag + DELTA_MAG, max_mag + DELTA_MAG, DELTA_MAG)
    cmap = plt.get_cmap(colormap)
    palette = ColorPalette.fromColorMap("mag", z0, z1, cmap)

    colors = []
    for zval in np.arange(min_mag, max_mag + 0.5, 0.5):
        tcolor = palette.getDataColor(zval, "hex")
        colors.append(tcolor)
    cmap2 = mpl.colors.ListedColormap(colors)

    for eventid in eventids:
        emag = event_table[event_table["id"] == eventid].magnitude.to_numpy()[0]
        norm_mag = (emag - min_mag) / (max_mag - min_mag)
        color = cmap2(norm_mag)
        erows = imc_table[imc_table["EarthquakeId"] == eventid]
        distance = erows[distance_metric]
        imtdata = erows[imt]
        ax.loglog(distance, imtdata, mfc=color, mec="k", marker="o", linestyle="None")

    ax.set_xlabel(f"{distance_metric} (km)")
    ax.set_ylabel(f"{imt} ({units})")

    bounds = np.arange(min_mag, max_mag + 1.0, 0.5)
    norm = mpl.colors.BoundaryNorm(bounds, cmap2.N)

    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="3%", pad=0.05)

    mpl.colorbar.ColorbarBase(
        cax,
        cmap=cmap2,
        norm=norm,
        ticks=bounds,  # optional
        spacing="proportional",
        orientation="vertical",
    )

    plt.sca(ax)
    plt.suptitle("%s vs %s (#eqks=%i)" % (imt, distance_metric, len(eventids)))
    plt.title(f"for component {imc}")

    plt.savefig(filename)


def plot_moveout(
    streams,
    epilat,
    epilon,
    orientation=None,
    max_dist=None,
    figsize=(10, 15),
    file=None,
    minfontsize=14,
    normalize=True,
    factor=0.2,
    alpha=0.25,
):
    """
    Create moveout plot.

    Args:
        streams (StreamCollection):
            StreamCollection of acceleration data with units of gal (cm/s/s).
        epilat (float):
            Epicenter latitude.
        epilon (float):
            Epicenter longitude.
        orientation (str):
            Orientation code (str) of each stream to view. Default is None.
            If None, then the orientation code with the highest number of
            traces will be used.
        max_dist (float):
            Maximum distance (in km) to plot. Default is 200 km.
        figsize (tuple):
            Tuple of height and width. Default is (10, 15).
        file (str):
            File where the image will be saved. Default is None.
        minfontsize (int):
            Minimum font size. Default is 14.
        normalize (bool):
            Normalize the data. Default is True.
        factor (int, float):
            Factor for scaling the trace. Default is 0.2, meaning that the
            trace with the greatest amplitude variation will occupy 20% of the
            vertical space in the plot.
        alpha (float):
            Alpha value for plotting the traces.

    Returns:
        tuple: (Figure, matplotlib.axes._subplots.AxesSubplot)
    """
    if len(streams) < 1:
        raise Exception("No streams provided.")

    fig, ax = plt.subplots(figsize=figsize)

    # If no channel is given, then find the orientation code with the greatest
    # number of traces
    if orientation is None:
        orientation_codes = []
        for st in streams:
            if st.passed:
                for tr in st:
                    orientation_codes.append(tr.stats.channel[-1])
        for i, code in enumerate(orientation_codes):
            if code == "1":
                orientation_codes[i] = "N"
            if code == "2":
                orientation_codes[i] = "E"
            if code == "3":
                orientation_codes[i] = "Z"
        channel_counter = Counter(orientation_codes)
        if channel_counter:
            orientation = max(channel_counter, key=channel_counter.get)
        else:
            return (fig, ax)

    valid_channels = []
    if orientation in ["N", "1"]:
        valid_channels = ["N", "1"]
    elif orientation in ["E", "2"]:
        valid_channels = ["E", "2"]
    elif orientation in ["Z", "3"]:
        valid_channels = ["Z", "3"]

    # Create a copy of the streams to avoid modifying the data when normalizing
    streams_copy = copy.deepcopy(streams)

    # Determine the distance and amplitude variation for scaling
    distances = []
    max_amp_variation = 0
    for st in streams:
        if st.passed:
            dist = (
                gps2dist_azimuth(
                    st[0].stats.coordinates["latitude"],
                    st[0].stats.coordinates["longitude"],
                    epilat,
                    epilon,
                )[0]
                / 1000.0
            )
            max_amp_var_st = 0
            for tr in st:
                amp_var_tr = abs(max(tr.data) - min(tr.data))
                if normalize:
                    amp_var_tr *= dist
                if amp_var_tr > max_amp_var_st:
                    max_amp_var_st = amp_var_tr
            if max_dist is not None:
                if dist < max_dist:
                    distances.append(dist)
                    if max_amp_var_st > max_amp_variation:
                        max_amp_variation = max_amp_var_st
            else:
                distances.append(dist)
                if max_amp_var_st > max_amp_variation:
                    max_amp_variation = max_amp_var_st

    if distances:
        scale = max(distances) * factor / max_amp_variation
    else:
        return (fig, ax)

    nplot = 0
    for idx, stream in enumerate(streams_copy):
        if not stream.passed:
            continue
        for trace in stream:
            if trace.stats.channel[-1] not in valid_channels:
                continue
            lat = trace.stats.coordinates["latitude"]
            lon = trace.stats.coordinates["longitude"]
            distance = gps2dist_azimuth(lat, lon, epilat, epilon)[0] / 1000.0

            # Don't plot if past the maximum distance
            if max_dist is not None and distance > max_dist:
                continue

            # Multiply by distance to normalize
            if normalize:
                trace.data = trace.data.astype(float) * distance
            trace.data *= scale

            times = []
            start = trace.stats.starttime
            for time in trace.times():
                starttime = start
                td = datetime.timedelta(seconds=time)
                ti = starttime + td
                times += [ti.datetime]
            ax.plot(times, trace.data + distance, c="k", alpha=alpha)
            nplot += 1
    ax.invert_yaxis()
    ax.set_title(f"Orientation code: {orientation}", fontsize=minfontsize + 4)
    ax.set_ylabel("Epicentral distance (km)", fontsize=minfontsize)
    ax.yaxis.set_tick_params(labelsize=minfontsize - 2)
    plt.xticks([])

    # Get the x-coordinate for the time bar
    if nplot > 0:
        xmin, xmax = ax.get_xlim()
        xbar = num2date(xmin + 0.9 * (xmax - xmin))
        xlabel = num2date(xmin + 0.83 * (xmax - xmin))

        # Get the y-coordinates for the time bar and label
        ymax, ymin = ax.get_ylim()
        ybar = 0
        ylabel = 0.05 * (ymax - ymin)

        # Plot the time-scale bar
        plt.errorbar(
            xbar, ybar, xerr=datetime.timedelta(seconds=15), color="k", capsize=5
        )
        plt.text(xlabel, ylabel, "30 seconds", fontsize=minfontsize)

    if file is not None:
        fig.savefig(file, format="png")
    # plt.show()
    return (fig, ax)


def plot_oscillators(st, periods=[0.1, 2, 5, 10], file=None, show=False):
    """
    Produces a figure of the oscillator responses for a StationStream. The
    figure will plot the acceleration traces in the first row, and then an
    additional row for each oscillator period. The number of columns is the
    number of channels in the stream.

    Args:
        st (gmprocess.core.stationstream.StationStream):
            StaionStream of data.
        periods (list):
            A list of periods (floats, in seconds).
        file (str):
            File where the image will be saved. Default is None.
        show (bool):
            Show the figure. Default is False.
    """

    fig, axes = plt.subplots(
        nrows=len(periods) + 1, ncols=len(st), figsize=(4 * len(st), 2 * len(periods))
    )
    if len(st) == 1:
        # Ensure that axes is a 2D numpy array
        axes = axes.reshape(-1, 1)

    for i in range(axes.shape[0]):
        if i == 0:
            plot_st = st
            ylabel = "Acceleration (cm/s$^2$)"
            textstr = "T: %s s \nPGA: %.2g cm/s$^2$"
        else:
            prd = periods[i - 1]
            plot_st = get_spectral(prd, st)
            ylabel = "SA %s s (%%g)" % prd
            textstr = "T: %s s \nSA: %.2g %%g"

        for j, tr in enumerate(plot_st):
            ax = axes[i, j]
            dtimes = np.linspace(
                0, tr.stats.endtime - tr.stats.starttime, tr.stats.npts
            )
            ax.plot(dtimes, tr.data, "k", linewidth=0.5)

            # Get time and amplitude of max SA (using absolute value)
            tmax = dtimes[np.argmax(abs(tr.data))]
            sa_max = max(tr.data, key=abs)

            ax.axvline(tmax, c="r", ls="--")
            ax.scatter([tmax], [sa_max], c="r", edgecolors="k", zorder=10)
            ax.text(
                0.01, 0.98, textstr % (tmax, sa_max), transform=ax.transAxes, va="top"
            )

            if i == 0:
                ax.set_title(tr.id)
            if i == len(periods):
                ax.set_xlabel("Time (s)")
            ax.set_ylabel(ylabel)

    plt.tight_layout()

    if file is not None:
        plt.savefig(file)
    if show:
        plt.show()