"""Module for creating stream summary plots."""

import os
from pathlib import Path
import logging

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from obspy.core.utcdatetime import UTCDateTime

from gmprocess.waveform_processing import spectrum
from gmprocess.utils import constants
from gmprocess.utils.config import get_config

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


class SummaryPlot:
    """Class to make stream summary plot."""

    def __init__(self, st, st_raw, directory, event, config=None):
        """Stream summary plot.

        Args:
            st (gmprocess.core.stationtrace.StationStream):
                Stream of data.
            st_raw (gmprocess.core.stationtrace.StationStream):
                Raw stream of data.
            directory (str):
                Directory for saving plots.
            event (gmprocess.utils.scalar_event.ScalarEvent):
                Flattened subclass of Obspy's Event.
            config (dict):
                Configuration dictionary (or None). See get_config().

        """
        self.st = st
        self.st_raw = st_raw
        self.stream_id = st.get_id()
        self.directory = Path(directory)
        self.event = event
        self.config = config
        if config is None:
            self.config = get_config()

        # Compute velocity and displacement
        self.get_vel_disp()

        # Check if directory exists, and if not, create it.
        self.directory.mkdir(parents=True, exist_ok=True)

    def plot(self):
        "Make the figure"
        self.setup_figure()
        self.reftime = self.st_raw[0].stats.starttime
        self.endtime = self.st_raw[0].stats.endtime - self.reftime

        for i, idx in enumerate(self.channelidx):
            # i is the plot column index
            self.ax = self.axs[i]
            self.tr = self.st[idx]
            self.tr_raw = self.st_raw[idx] if self.st_raw else None
            self.tr_vel = self.st_vel[idx]
            self.tr_dis = self.st_dis[idx]
            if i > 2:
                logging.warning("Only plotting first 3 traces in stream.")
                break
            self.get_trace_info()
            self.compute_model_spectra()

            i_ax = i
            if self.tr_raw:
                self.ax = self.axs[i_ax]
                self.plot_raw()
                if i == 0:
                    self.ax.set_ylabel("Raw")

            # acceleration is plotted on first row of plots
            i_ax += self.ntrace
            self.ax = self.axs[i_ax]
            self.plot_acceleration()
            if i == 0:
                self.ax.set_ylabel("Acceleration (cm/s/s)")

            # velocity is plooted on second row of plots
            i_ax += self.ntrace
            self.ax = self.axs[i_ax]
            self.plot_velocity()
            if i == 0:
                self.ax.set_ylabel("Velocity (cm/s)")

            # displacement is plotted on third row of plots
            i_ax += self.ntrace
            self.ax = self.axs[i_ax]
            self.plot_displacement()
            if i == 0:
                self.ax.set_ylabel("Displacement (cm)")

            # Fourier spectra are plotted on fourth row of plots
            i_ax += self.ntrace
            self.ax = self.axs[i_ax]
            self.plot_spectra()
            if i == 0:
                self.ax.set_ylabel("Normalized Amplitude (cm*s$^{-1.5}$)")

            # SNR is plotted on fifth row of plots
            i_ax += self.ntrace
            self.ax = self.axs[i_ax]
            self.plot_snr()
            if i == 0:
                self.ax.set_ylabel("SNR")

        # Do not save files if running tests
        file_name = None
        if "CALLED_FROM_PYTEST" not in os.environ:
            file_name = self.directory / f"{self.event.id}_{self.stream_id}.png"
            plt.savefig(fname=file_name)
            plt.close("all")
        return file_name

    def get_vel_disp(self):
        "Compute velocity and displaement"
        self.st_vel = self.st.copy()
        for tr in self.st_vel:
            tr = tr.integrate(**self.config["integration"])

        # Compute displacement
        self.st_dis = self.st.copy()
        for tr in self.st_dis:
            tr = tr.integrate(**self.config["integration"]).integrate(
                **self.config["integration"]
            )

    def setup_figure(self):
        "Setup figure"
        nrows = 6
        self.ntrace = min(len(self.st), 3)
        fig = plt.figure(figsize=(3.9 * self.ntrace, 11))
        gs = fig.add_gridspec(nrows, self.ntrace, height_ratios=[1, 1, 1, 1, 2, 2])
        fig.subplots_adjust(
            left=0.08, right=0.98, hspace=0.3, wspace=0.25, top=0.97, bottom=0.05
        )
        self.axs = [plt.subplot(g) for g in gs]
        if self.st.passed:
            plt.suptitle(
                f"M{self.event.magnitude} {self.event.id} | {self.stream_id} (passed)",
                x=0.5,
                y=1.02,
            )
        else:
            plt.suptitle(
                f"M{self.event.magnitude} {self.event.id} | {self.stream_id} (failed)",
                color="red",
                x=0.5,
                y=1.02,
            )
        channels = [tr.stats.channel for tr in self.st]
        self.channelidx = np.argsort(channels).tolist()

    def get_trace_info(self):
        self.snr_dict = self.tr.get_cached("snr", missing_none=True)
        self.signal_dict = self.tr.get_cached("signal_spectrum", missing_none=True)
        self.noise_dict = self.tr.get_cached("noise_spectrum", missing_none=True)
        self.smooth_signal_dict = self.tr.get_cached(
            "smooth_signal_spectrum", missing_none=True
        )
        self.smooth_noise_dict = self.tr.get_cached(
            "smooth_noise_spectrum", missing_none=True
        )
        self.snr_conf = self.tr.get_parameter("snr_conf", missing_none=True)
        self.tail_conf = self.tr.get_parameter("tail_conf", missing_none=True)
        self.fit_spectra_dict = self.tr.get_parameter("fit_spectra", missing_none=True)

    def compute_model_spectra(self):
        if (self.fit_spectra_dict is not None) and (
            self.smooth_signal_dict is not None
        ):
            self.model_spec = spectrum.model(
                (
                    self.fit_spectra_dict["moment"],
                    self.fit_spectra_dict["stress_drop"],
                ),
                freq=np.array(self.smooth_signal_dict["freq"]),
                dist=self.fit_spectra_dict["epi_dist"],
                kappa=self.fit_spectra_dict["kappa"],
            )

    def plot_raw(self):
        trace_status = " (passed)" if self.tr.passed else " (failed)"
        trace_title = self.tr.get_id() + trace_status
        if self.tr.passed:
            self.ax.set_title(trace_title)
        else:
            self.ax.set_title(trace_title, color="red")

        dtimes = self.tr_raw.times(reftime=self.reftime)
        self.ax.plot(dtimes, self.tr_raw.data, "k", linewidth=0.5)
        self.ax.tick_params(axis="both", which="major", labelsize=5)
        self.ax.set_xlim([0, self.endtime])

    def plot_acceleration(self):
        pga = np.max(np.abs(self.tr.data)) / constants.UNIT_CONVERSIONS["g"]
        dtimes = self.tr.times(reftime=self.reftime)
        self.ax.plot(dtimes, self.tr.data, "k", linewidth=0.5)
        self.ax.tick_params(axis="both", which="major", labelsize=5)

        self.label_peak("PGA", pga, "g")
        self.draw_split_time()
        self.ax.set_xlim([0, self.endtime])

    def plot_velocity(self):
        pgv = np.max(np.abs(self.tr_vel.data))
        dtimes = self.tr_vel.times(reftime=self.reftime)
        self.ax.plot(dtimes, self.tr_vel.data, "k", linewidth=0.5)
        self.ax.tick_params(axis="both", which="major", labelsize=5)

        self.label_peak("PGV", pgv, "cm/s")
        self.draw_split_time()
        self.draw_tail_check(self.tr_vel, type="vel")
        self.ax.set_xlim([0, self.endtime])

    def plot_displacement(self):
        pgd = np.max(np.abs(self.tr_dis.data))
        dtimes = self.tr_dis.times(reftime=self.reftime)
        self.ax.plot(dtimes, self.tr_dis.data, "k", linewidth=0.5)
        self.ax.tick_params(axis="both", which="major", labelsize=5)

        self.label_peak("PGD", pgd, "cm")
        self.draw_split_time()
        self.ax.set_xlabel("Time (s)")
        self.draw_tail_check(self.tr_dis, type="dis")
        self.ax.set_xlim([0, self.endtime])

    def label_peak(self, name, value, units):
        self.ax.text(
            0.95,
            0.95,
            f"{name}: {value:.3g} {units}",
            transform=self.ax.transAxes,
            va="top",
            ha="right",
            color="0.5",
        )

    def draw_split_time(self):
        if self.tr.has_parameter("signal_split"):
            split_dict = self.tr.get_parameter("signal_split")
            sptime = UTCDateTime(split_dict["split_time"])
            dsec = sptime - self.reftime
            self.ax.axvline(dsec, color="red", linestyle="dashed")

    def draw_tail_check(self, tr, type="vel"):
        if self.tail_conf is not None:
            utc_start = UTCDateTime(self.tail_conf["start_time"])
            tail_start = utc_start - self.tr.stats.starttime
            tail_end = self.tr.stats.endtime - self.tr.stats.starttime
            abs_max_vel = np.max(np.abs(tr.data))
            if type == "vel":
                ratio = self.tail_conf["max_vel_ratio"]
            elif type == "dis":
                ratio = self.tail_conf["max_dis_ratio"]
            else:
                raise ValueError("Unsupported tail check type.")
            threshold = abs_max_vel * ratio
            rect = patches.Rectangle(
                (tail_start, -threshold),
                tail_end - tail_start,
                2 * threshold,
                linewidth=0,
                edgecolor="none",
                facecolor="#3cfa8b",
            )
            self.ax.add_patch(rect)

    def plot_spectra(self):
        signal_norm_factor = (
            self.tr.get_parameter("signal_spectrum")["duration"] ** 0.5
            if self.tr.has_parameter("signal_spectrum")
            else 1.0
        )
        noise_norm_factor = (
            self.tr.get_parameter("noise_spectrum")["duration"] ** 0.5
            if self.tr.has_parameter("noise_spectrum")
            else 1.0
        )

        # Raw signal spec
        if (self.signal_dict is not None) and np.any(self.signal_dict["spec"] > 0):
            self.ax.loglog(
                self.signal_dict["freq"],
                self.signal_dict["spec"] / signal_norm_factor,
                color="lightblue",
                alpha=0.5,
            )

        # Raw noise spec
        if (self.noise_dict is not None) and np.any(self.noise_dict["spec"] > 0):
            self.ax.loglog(
                self.noise_dict["freq"],
                self.noise_dict["spec"] / noise_norm_factor,
                color="salmon",
                alpha=0.5,
            )

        # Smoothed signal spec
        if (self.smooth_signal_dict is not None) and np.any(
            self.smooth_signal_dict["spec"] > 0
        ):
            self.ax.loglog(
                self.smooth_signal_dict["freq"],
                self.smooth_signal_dict["spec"] / signal_norm_factor,
                color="blue",
                alpha=0.8,
                label="Signal",
            )

        # Smoothed noise spec
        if (self.smooth_noise_dict is not None) and np.any(
            self.smooth_noise_dict["spec"] > 0
        ):
            self.ax.loglog(
                self.smooth_noise_dict["freq"],
                self.smooth_noise_dict["spec"] / noise_norm_factor,
                color="red",
                alpha=0.8,
                label="Noise",
            )

        if (self.fit_spectra_dict is not None) and (
            self.smooth_signal_dict is not None
        ):
            # Model spec
            self.ax.loglog(
                self.smooth_signal_dict["freq"],
                self.model_spec / signal_norm_factor,
                color="black",
                linestyle="dashed",
            )

            # Corner frequency
            self.ax.axvline(
                self.fit_spectra_dict["f0"], color="black", linestyle="dashed"
            )

        self.ax.autoscale(enable=True, axis="x", tight=True)
        self.xlim = self.ax.get_xlim()
        ymin, ymax = self.ax.get_ylim()
        if ymin < 1e-5 * ymax:
            ymin = 1e-5 * ymax
        self.ax.set_ylim([ymin, ymax])

    def plot_snr(self):
        if "corner_frequencies" in self.tr.get_parameter_keys():
            hp = self.tr.get_parameter("corner_frequencies")["highpass"]
            lp = self.tr.get_parameter("corner_frequencies")["lowpass"]
            self.ax.axvline(hp, color="black", ls="dashed", label="Highpass")
            self.ax.axvline(lp, color="black", ls="dashed", label="Lowpass")

        if self.snr_conf is not None:
            self.ax.axhline(self.snr_conf["threshold"], color="0.75", ls="dotted", lw=2)
            self.ax.axvline(self.snr_conf["max_freq"], color="0.75", lw=2, ls="dashed")
            self.ax.axvline(self.snr_conf["min_freq"], color="0.75", lw=2, ls="dashed")

        if self.snr_dict is not None:
            self.ax.loglog(self.snr_dict["freq"], self.snr_dict["snr"], label="SNR")

        self.ax.set_xlabel("Frequency (Hz)")
        self.ax.set_xlim(self.xlim)
        ymin, ymax = self.ax.get_ylim()
        if ymin < 0.1:
            ymin = 0.1
        self.ax.set_ylim([ymin, ymax])
