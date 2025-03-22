"""Module for holding classes for transformation waveform metric processing steps."""

import numpy as np

from obspy import Trace
from obspy.signal.util import next_pow_2

from esi_core.gmprocess.waveform_processing.smoothing import konno_ohmachi

from gmprocess.metrics.oscillator import calculate_spectrals
from gmprocess.metrics.waveform_metric_calculator_component_base import BaseComponent
from gmprocess.metrics import containers
from gmprocess.metrics.waveform_metric_component import Channels
from gmprocess.metrics.utils import component_to_channel
from gmprocess.utils.constants import GAL_TO_PCTG
import gmprocess.metrics.waveform_metric_component as wm_comp


class Integrate(BaseComponent):
    """Integrate the traces."""

    outputs = {}
    INPUT_CLASS = [containers.Trace]

    def calculate(self):
        new_traces = []
        for trace in self.prior_step.output.traces:
            new_traces.append(trace.copy().integrate(**self.parameters))
        self.output = containers.Trace(new_traces)

    @staticmethod
    def get_type_parameters(config):
        return config["integration"]


class Arias(BaseComponent):
    """Compute the Arias intensity."""

    outputs = {}
    INPUT_CLASS = [containers.Trace]

    def calculate(self):
        new_traces = []
        for trace in self.prior_step.output.traces:
            new_trace = trace.copy()
            # Convert from cm/s/s to m/s/s
            new_trace.data *= 0.01
            # Square acceleration
            new_trace.data *= new_trace.data
            # Integrate, and force time domain to avoid frequency-domain artifacts that
            # creat negative values.
            # self.parameters["frequency"] = False
            new_trace.integrate(frequency=False)
            # Multiply by constants
            new_trace.data = new_trace.data * np.pi * GAL_TO_PCTG / 2

            new_traces.append(new_trace)
        self.output = containers.Trace(new_traces)


def calculate_trace_oscillator(parameters, prior_step):
    """Helper function to compute the oscillator response for a trace.

    Args:
        parameters (dict):
            Dictionary of oscillator processing parameters (periods, damping).
        prior_step (BaseComponent):
            Result of the prior processing step.

    """
    per = parameters["periods"]
    damp = parameters["damping"]
    n_traces = len(prior_step.output.traces)
    acceleration_list = np.zeros((n_traces,))
    velocity_list = np.zeros((n_traces,))
    displacement_list = np.zeros((n_traces,))
    stats_list = []
    for i_trace, trace in enumerate(prior_step.output.traces):
        osc_results = calculate_spectrals(trace.copy(), period=per, damping=damp)
        acceleration_list[i_trace] = np.max(np.abs(osc_results[0]))
        velocity_list[i_trace] = np.max(np.abs(osc_results[1]))
        displacement_list[i_trace] = np.max(np.abs(osc_results[2]))
        stats_list.append(dict(trace.stats))

    output = containers.Oscillator(
        period=per,
        damping=damp,
        oscillator_dt=osc_results[0][4],
        acceleration=acceleration_list,
        velocity=velocity_list,
        displacement=displacement_list,
        stats_list=stats_list,
    )
    return output


def calculate_rotd_oscillator(parameters, prior_step):
    """Helper function to compute the rotd oscillator response.

    Args:
        parameters (dict):
            Dictionary of oscillator processing parameters (periods, damping).
        prior_step (BaseComponent):
            Result of the prior processing step.
    """
    per = parameters["periods"]
    damp = parameters["damping"]
    n_orientations = prior_step.output.matrix.shape[0]
    acceleration_matrix = np.zeros((n_orientations,))
    velocity_matrix = np.zeros((n_orientations,))
    displacement_matrix = np.zeros((n_orientations,))
    for i_orientation, trace_data in enumerate(prior_step.output.matrix):
        temp_trace = Trace(trace_data, prior_step.output.stats)
        osc_results = calculate_spectrals(temp_trace, period=per, damping=damp)
        acceleration_matrix[i_orientation] = np.max(np.abs(osc_results[0]))
        velocity_matrix[i_orientation] = np.max(np.abs(osc_results[1]))
        displacement_matrix[i_orientation] = np.max(np.abs(osc_results[2]))

    output = containers.RotDOscillator(
        period=per,
        damping=damp,
        oscillator_dt=osc_results[0][4],
        acceleration_matrix=acceleration_matrix,
        velocity_matrix=velocity_matrix,
        displacement_matrix=displacement_matrix,
        stats=prior_step.output.stats,
    )
    return output


class TraceOscillator(BaseComponent):
    """Return the oscillator response of the input traces.

    self.output: containers.Oscillator
    """

    outputs = {}
    INPUT_CLASS = [containers.Trace]

    def calculate(self):
        self.output = calculate_trace_oscillator(
            parameters=self.parameters, prior_step=self.prior_step
        )

    @staticmethod
    def get_type_parameters(config):
        return {
            "periods": config["metrics"]["type_parameters"]["sa"]["periods"],
            "damping": config["metrics"]["type_parameters"]["sa"]["damping"],
        }


class RotDOscillator(BaseComponent):
    """Return the oscillator response of traces that have undergone a RotD rotation."""

    outputs = {}
    INPUT_CLASS = [containers.RotDTrace]

    def calculate(self):
        self.output = calculate_rotd_oscillator(
            parameters=self.parameters, prior_step=self.prior_step
        )

    @staticmethod
    def get_type_parameters(config):
        return {
            "periods": config["metrics"]["type_parameters"]["sa"]["periods"],
            "damping": config["metrics"]["type_parameters"]["sa"]["damping"],
        }


class FourierAmplitudeSpectra(BaseComponent):
    """Return the Fourier amplitude spectra of the input traces."""

    outputs = {}
    INPUT_CLASS = [containers.Trace]

    def calculate(self):
        nfft = self._get_nfft(self.prior_step.output.traces[0])
        spectra_list = []
        stats_list = []
        for trace in self.prior_step.output.traces:
            spectra1, freqs1 = self._compute_fft(trace, nfft)
            spectra_list.append(spectra1)
            stats_list.append(trace.stats)
        self.output = containers.FourierSpectra(
            frequency=freqs1,
            fourier_spectra=spectra_list,
            stats_list=stats_list,
        )

    @staticmethod
    def get_type_parameters(config):
        return config["metrics"]["type_parameters"]["fas"]

    @staticmethod
    def _compute_fft(trace, nfft):
        dt = trace.stats.delta
        spec = abs(np.fft.rfft(trace.data, n=nfft)) * dt
        freqs = np.fft.rfftfreq(nfft, dt)
        return spec, freqs

    def _get_nfft(self, trace):
        """Get number of points in the FFT.

        If allow_nans is False, returns the number of points for the FFT that
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
            bw = self.parameters["smoothing_parameter"]
            nyquist = 0.5 * trace.stats.sampling_rate
            min_freq = self.parameters["frequencies"]["start"]
            df = (min_freq * 10 ** (3.0 / bw)) - (min_freq / 10 ** (3.0 / bw))
            nfft = max(len(trace.data), nyquist / df)
        return next_pow_2(nfft)


class SmoothSpectra(BaseComponent):
    """Return the smoothed Fourier amplitude spectra of the input spectra."""

    outputs = {}
    INPUT_CLASS = [containers.CombinedSpectra, containers.FourierSpectra]

    def calculate(self):
        if isinstance(self.prior_step.output, containers.FourierSpectra):
            nspec = len(self.prior_step.output.fourier_spectra)
            ko_spec_list = []
            for i in range(nspec):
                ko_spec, ko_freq = self._smooth_spectrum(
                    self.prior_step.output.fourier_spectra[i],
                    self.prior_step.output.frequency,
                )
                ko_spec_list.append(ko_spec)

            self.output = containers.FourierSpectra(
                frequency=ko_freq,
                fourier_spectra=ko_spec_list,
                stats_list=self.prior_step.output.stats_list,
            )
        elif isinstance(self.prior_step.output, containers.CombinedSpectra):
            ko_spec, ko_freq = self._smooth_spectrum(
                self.prior_step.output.fourier_spectra,
                self.prior_step.output.frequency,
            )
            self.output = containers.CombinedSpectra(
                frequency=ko_freq,
                fourier_spectra=ko_spec,
            )
        else:
            raise TypeError("Unsupported input class for SmoothSpectra component.")

    @staticmethod
    def get_type_parameters(config):
        return config["metrics"]["type_parameters"]["fas"]

    def get_component_results(self):
        if isinstance(self.prior_step.output, containers.CombinedSpectra):
            # return get_channel_outputs(self)
            # return get_component_output(self, str(wm_comp.QuadraticMean()))
            return ([self.output], [str(wm_comp.QuadraticMean())])
        elif isinstance(self.prior_step.output, containers.FourierSpectra):
            vals = []
            coms = []
            channels = [stats["channel"] for stats in self.output.stats_list]
            _, chan2comp = component_to_channel(channels)
            for spec, chan, stats in zip(
                self.output.fourier_spectra, channels, self.output.stats_list
            ):
                vals.append(
                    containers.FourierSpectra(
                        frequency=self.output.frequency,
                        fourier_spectra=[spec],
                        stats_list=[stats],
                    )
                )
                coms.append(str(Channels(chan, chan2comp[chan])))
        else:
            raise TypeError("Unsupported input class for SmoothSpectra component.")
        return (vals, coms)

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
        smoothing_parameter = self.parameters["smoothing_parameter"]
        freq_conf = self.parameters["frequencies"]
        ko_freqs = np.logspace(
            np.log10(freq_conf["start"]), np.log10(freq_conf["stop"]), freq_conf["num"]
        )
        # An array to hold the output
        spec_smooth = np.empty_like(ko_freqs)

        # Konno Omachi Smoothing
        konno_ohmachi.konno_ohmachi_smooth(
            spec.astype(np.double), freqs, ko_freqs, spec_smooth, smoothing_parameter
        )
        # Set any results outside of range of freqs to nans
        spec_smooth[(ko_freqs > np.max(freqs)) | (ko_freqs < np.min(freqs))] = np.nan
        return spec_smooth, ko_freqs
