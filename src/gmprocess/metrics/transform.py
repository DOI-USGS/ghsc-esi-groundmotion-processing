"""Module for holding classes for transformation waveform metric processing steps."""

import itertools

import numpy as np

from obspy import Trace
from obspy.signal.util import next_pow_2

from esi_core.gmprocess.waveform_processing.smoothing import konno_ohmachi

from gmprocess.metrics.oscillator import calculate_spectrals
from gmprocess.metrics.metric_component_base import Component
from gmprocess.metrics import containers
from gmprocess.utils.constants import GAL_TO_PCTG


class Integrate(Component):
    """Integrate the traces."""

    outputs = {}

    def calculate(self):
        new_traces = []
        for trace in self.parent.output.traces:
            new_traces.append(trace.copy().integrate(**self.parameters))
        self.output = containers.Trace(new_traces)

    @staticmethod
    def get_parameters(config):
        return [config["integration"]]


class TraceOscillator(Component):
    """Return the oscillator response of the input traces."""

    outputs = {}

    INPUT_CLASS = containers.Trace

    def calculate(self):
        iper = self.parameters["periods"]
        idamp = self.parameters["damping"]
        all_oscillators = []
        for per, damp in itertools.product(iper, idamp):
            oscillator_list = []
            for trace in self.parent.output.traces:
                sa_results = calculate_spectrals(trace.copy(), period=per, damping=damp)
                acc_sa = sa_results[0]
                acc_sa *= GAL_TO_PCTG
                oscillator_list.append(acc_sa)
            all_oscillators.append(
                containers.Oscillator(
                    period=per,
                    damping=damp,
                    oscillator_dt=sa_results[4],
                    oscillators=oscillator_list,
                )
            )
        self.output = containers.OscillatorCollection(all_oscillators)

    @staticmethod
    def get_parameters(config):
        return [config["metrics"]["sa"]]


class RotDOscillator(Component):
    """Return the oscillator response of traces that have undergone a RotD rotation."""

    outputs = {}

    INPUT_CLASS = containers.RotDTrace

    def calculate(self):
        iper = self.parameters["periods"]
        idamp = self.parameters["damping"]
        all_oscillators = []
        for per, damp in itertools.product(iper, idamp):
            oscillator_list = []
            for trace_data in self.parent.output.trace_matrix:
                temp_trace = Trace(trace_data, self.parent.output.stats)
                sa_results = calculate_spectrals(temp_trace, period=per, damping=damp)
                acc_sa = sa_results[0]
                acc_sa *= GAL_TO_PCTG
                oscillator_list.append(acc_sa)
            all_oscillators.append(
                containers.RotDOscillator(
                    period=per,
                    damping=damp,
                    oscillator_dt=sa_results[4],
                    oscillator_matrix=np.stack(oscillator_list),
                )
            )
        self.output = containers.RotDOscillatorCollection(all_oscillators)

    @staticmethod
    def get_parameters(config):
        return [config["metrics"]["sa"]]


class FourierAmplitudeSpectra(Component):
    """Return the Fourier amplitude spectra of the input traces."""

    outputs = {}

    def calculate(self):
        nfft = self._get_nfft(self.parent.output.traces[0])
        spectra_list = []
        for trace in self.parent.output.traces:
            spectra1, freqs1 = self._compute_fft(trace, nfft)
            spectra_list.append(spectra1)
        self.output = containers.FourierSpectra(
            frequency=freqs1,
            fourier_spectra=spectra_list,
        )

    @staticmethod
    def get_parameters(config):
        return [config["metrics"]["fas"]]

    @staticmethod
    def _compute_fft(trace, nfft):
        dt = trace.stats.delta
        spec = abs(np.fft.rfft(trace.data, n=nfft)) * dt
        freqs = np.fft.rfftfreq(nfft, dt)
        return spec, freqs

    def _get_nfft(self, trace):
        """Get number of points in the FFT.

        If allow_nans is True, returns the number of points for the FFT that
        will ensure that the Fourier Amplitude Spectrum can be computed without
        returning NaNs (due to the spectral resolution requirements of the
        Konno-Ohmachi smoothing). Otherwise, just use the length of the trace
        for the number points. This always returns the next highest power of 2.

        Returns:
            int: Number of points for the FFT.
        """

        if self.parameters["allow_nans"]:
            nfft = len(trace.data)
        else:
            bw = self.parameters["bandwidth"]
            nyquist = 0.5 * trace.stats.sampling_rate
            min_freq = self.parameters["frequencies"]["start"]
            df = (min_freq * 10 ** (3.0 / bw)) - (min_freq / 10 ** (3.0 / bw))
            nfft = max(len(trace.data), nyquist / df)
        return next_pow_2(nfft)


class SmoothSpectra(Component):
    """Return the smoothed Fourier amplitude spectra of the input spectra."""

    outputs = {}

    def calculate(self):
        ko_spec, ko_freq = self._smooth_spectrum(
            self.parent.output.fourier_spectra,
            self.parent.output.frequency,
        )
        self.output = containers.CombinedSpectra(
            frequency=ko_freq,
            fourier_spectra=ko_spec,
        )

    @staticmethod
    def get_parameters(config):
        return [config["metrics"]["fas"]]

    def _smooth_spectrum(self, spec, freqs):
        """
        Smooths the amplitude spectrum following the algorithm of
        Konno and Ohmachi.

        Args:
            spec (numpy.ndarray):
                Spectral amplitude data.
            freqs (numpy.ndarray):
                Frequencies.

        Returns:
            numpy.ndarray: Smoothed amplitude data and frequencies.
        """
        bandwidth = self.parameters["bandwidth"]
        freq_conf = self.parameters["frequencies"]
        ko_freqs = np.logspace(
            np.log10(freq_conf["start"]), np.log10(freq_conf["stop"]), freq_conf["num"]
        )
        # An array to hold the output
        spec_smooth = np.empty_like(ko_freqs)

        # Konno Omachi Smoothing
        konno_ohmachi.konno_ohmachi_smooth(
            spec.astype(np.double), freqs, ko_freqs, spec_smooth, bandwidth
        )
        # Set any results outside of range of freqs to nans
        spec_smooth[(ko_freqs > np.max(freqs)) | (ko_freqs < np.min(freqs))] = np.nan
        return spec_smooth, ko_freqs
