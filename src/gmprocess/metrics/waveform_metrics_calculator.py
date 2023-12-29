#!/usr/bin/env python
"""Module for calculating waveform metrics.

# WaveformMetricCalculator
This is the primary class for calculating the metrics for an input stream.

# Component
This is a base class for methods like transforms, reductions, rotations, combinations.
- Component child classes have attributes "parent" and "output".
- The "parent" attribute holds the Component child class for the previous processing
  step.
- The "output" attribute holds a dataclass, such as TraceContainer, or ScalarContainer.
- All Component class have a "calculate" method that defines the calculations for that
  processing step, places the results in an appropriate dataclass, and places that
  dataclass in the "output" attribute.

# InputDataComponent
This is a special child of Component for holding the input data. It's "parent" attribute
is None and the "calculate" method is a no-op.

# WaveformMetricCalculator Details
- Initially, "result" holds the InputDataComponent, which is handed off as output
  for the next processing step.
- "metric_dict" is a dictionary that holds results for all completed steps.
- "metric_dict" can be inspected by loooking at the parent/output attributes, e.g.

    metric_dict["test1"]

  is an object with the type of the last step, and the previous step can be accessed
  with

    metric_dict["test1"].parent

  while the data resulting from the step can be accessed with

    metric_dict["test1"].output

  And the result of the previous step can be accessed with

    metric_dict["test1"].parent.output

  This continues recursively until the "parent" attribute is Null, which is the initial
  input data.

  The "outputs" attibute is a shared dictionary across all steps that caches the
  and are re-used

"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
import copy
import logging
import json
import itertools

import numpy as np
from obspy.signal.util import next_pow_2
from obspy import Trace

from esi_core.gmprocess.waveform_processing.smoothing import konno_ohmachi

from gmprocess.core.stationtrace import StationTrace
from gmprocess.metrics.transform.oscillator import new_and_improved_calculate_spectrals
from gmprocess.utils.constants import GAL_TO_PCTG


class WaveformMetricCalculator:
    """Class for calculating waveform metrics"""

    def __init__(self, stream, steps, config):
        """WaveformMetricCalculator initializer.

        Args:
            stream (StationStream):
                A StationStream object.
            steps (dict):
                A dictionary, in which the key are the name of the metric and the value
                value of that key is the
            config (dict):
                Config options.
        """
        self.stream = stream
        self.steps = steps
        self.config = config
        self.metric_dict = None

        self.input_data = InputDataComponent(
            TraceContainer(
                [stream.select(channel="HN1")[0], stream.select(channel="HN2")[0]]
            )
        )

    def calculate(self):
        """Calculate waveform metrics."""
        result = self.input_data
        self.metric_dict = {}

        for metric, metric_steps in self.steps.items():
            logging.info(f"Metric: {metric}")
            result = self.input_data
            for metric_step in metric_steps:
                logging.info(f"Metric step: {metric_step}")
                metric_step_class = globals()[metric_step]
                parameter_list = metric_step_class.get_parameters(self.config)
                self.validate_params(parameter_list)
                for params in parameter_list:
                    result = metric_step_class(result, params)
            self.metric_dict[metric] = result

    def validate_params(self, parameter_list):
        """Validate that the parameter_list has the correct structure.

        Needs to be a list of dictionaries to ensure the appropriate key is generated
        for Component.outputs.
        """
        if not isinstance(parameter_list, list):
            raise ValueError("parameter_list must be a list.")
        for pdict in parameter_list:
            if not isinstance(pdict, dict):
                raise ValueError("parameter_list element must be a dictionary.")


@dataclass(repr=False)
class TraceContainer:
    """Class for holding StationTrace data."""

    traces: list[StationTrace]


@dataclass(repr=False)
class ReferenceValue:
    """Class for holding a scalar with supporting stats dictionary."""

    value: float
    stats: dict

    def __repr__(self):
        return f"ReferenceValue: {self.value:.4g}"


@dataclass(repr=False)
class ScalarContainer:
    """Class for holding scalar metric data."""

    traces: list[ReferenceValue]

    def __repr__(self):
        list_str = ", ".join([ref for ref in self.traces])
        return f"ScalarContainer({list_str})"


@dataclass(repr=False)
class CombinedScalarContainer:
    """Class for holding combined scalar metric data."""

    trace: ReferenceValue

    def __repr__(self):
        return f"CombinedScalarContainer(trace: {self.trace})"


@dataclass(repr=False)
class FourierSpectraContainer:
    """Class for holding Fourier Spectra metric data."""

    frequency: np.ndarray
    fourier_spectra: list[np.ndarray]


@dataclass(repr=False)
class CombinedSpectraContainer:
    """Class for holding Fourier Spectra combined metric data."""

    frequency: np.ndarray
    fourier_spectra: np.ndarray


@dataclass(repr=False)
class OscillatorContainer:
    """Class for holding oscillator time history for a given TraceContainer."""

    period: float
    damping: float
    oscillators: list[np.ndarray]
    oscillator_dt: float


@dataclass(repr=False)
class RotDOscillatorContainer:
    """Class for holding oscillator time history for a given TraceRotDContainer."""

    period: float
    damping: float
    oscillator_matrix: np.ndarray
    oscillator_dt: float


@dataclass(repr=False)
class OscillatorCollection:
    """Class for holding a colleciton of OscillatorContainers."""

    oscillators: list[OscillatorContainer]


@dataclass(repr=False)
class RotDOscillatorCollection:
    """Class for holding a colleciton of OscillatorContainers."""

    oscillators: list[RotDOscillatorContainer]


@dataclass(repr=False)
class TraceRotDContainer:
    """Class for holding traces rotated using the RotD method."""

    trace_matrix: np.ndarray
    stats: dict


class Component(ABC):
    """Abstract base class for processing components."""

    def __init__(self, input_data, parameters=None):
        """Initialize a Component.

        Args:
            input_data (Component):
                A Component object that contains the "parent" attribute, which is the
                Component of the previous step (or None if there is not previous step).
            parameters (dict):
                Dictionary of processing parameters required by the Component.
        """
        self.parent = input_data
        self.parameters = parameters
        # - we need to define a key for self.outputs, which is unique for a given
        #   input_data object as well as any processing parameters for the current
        #   calculation.
        # - think of this as a table lookup (the table is self.outputs) and the table
        #   is unique for each sequence of steps (e.g., ["Integrate", "TraceMax"]).
        param_str = json.dumps(self.parameters)
        output_key = str(id(self.parent)) + str(hash(param_str))
        if output_key in self.outputs:
            # Note that self.output is a list of Component objects.
            self.output = copy.copy(self.outputs[output_key])
        else:
            self.calculate()
            self.outputs[output_key] = self.output

    def __repr__(self):
        step_list = [type(self).__name__]
        step = self.parent
        while step:
            step_list.append(type(step).__name__)
            step = step.parent
        step_list.reverse()
        return ".".join(step_list)

    @abstractmethod
    def calculate(self):
        pass

    @staticmethod
    def get_parameters(config):
        """Populate a list of params for a metric Component.

        This needs to be a list of dictionaries.

        The default is a list with an empty dictionary because not all child classes
        need parameters.

        Args:
            config (dict):
                Config dictionary.
        """
        return [{}]


class InputDataComponent(Component):
    outputs = {}

    def __init__(self, input_data):
        super().__init__(None)
        self.output = input_data

    def calculate(self):
        self.output = self.parent


class Integrate(Component):
    outputs = {}

    def calculate(self):
        logging.info("** Calculating Integrate")
        new_traces = []
        for trace in self.parent.output.traces:
            new_traces.append(trace.copy().integrate(**self.parameters))
        self.output = TraceContainer(new_traces)

    @staticmethod
    def get_parameters(config):
        return [config["integration"]]


class FourierAmplitudeSpectra(Component):
    outputs = {}

    def calculate(self):
        logging.info("** Calculating FourierAmplitudeSpectra")
        nfft = self._get_nfft(self.parent.output.traces[0])
        spectra_list = []
        for trace in self.parent.output.traces:
            spectra1, freqs1 = self._compute_fft(trace, nfft)
            spectra_list.append(spectra1)
        self.output = FourierSpectraContainer(
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


class SpectraQuadraticMean(Component):
    outputs = {}

    def calculate(self):
        logging.info("** Calculating SpectraQuadraticMean")
        fas_matrix = np.stack(self.parent.output.fourier_spectra)
        nrow = fas_matrix.shape[0]
        quad_mean = np.sqrt(np.sum(fas_matrix**2, axis=0) / nrow)
        self.output = CombinedSpectraContainer(
            frequency=self.parent.output.frequency,
            fourier_spectra=quad_mean,
        )


class SmoothSpectra(Component):
    outputs = {}

    def calculate(self):
        logging.info("** Calculating SmoothSpectra")
        ko_spec, ko_freq = self._smooth_spectrum(
            self.parent.output.fourier_spectra,
            self.parent.output.frequency,
        )
        self.output = CombinedSpectraContainer(
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


class TraceOscillator(Component):
    outputs = {}

    INPUT_CLASS = TraceContainer

    def calculate(self):
        logging.info("** Calculating TraceOscillator")
        iper = self.parameters["periods"]
        idamp = self.parameters["damping"]
        all_oscillators = []
        for per, damp in itertools.product(iper, idamp):
            oscillator_list = []
            for trace in self.parent.output.traces:
                sa_results = new_and_improved_calculate_spectrals(
                    trace.copy(), period=per, damping=damp
                )
                acc_sa = sa_results[0]
                acc_sa *= GAL_TO_PCTG
                oscillator_list.append(acc_sa)
            all_oscillators.append(
                OscillatorContainer(
                    period=per,
                    damping=damp,
                    oscillator_dt=sa_results[4],
                    oscillators=oscillator_list,
                )
            )
        self.output = OscillatorCollection(all_oscillators)

    @staticmethod
    def get_parameters(config):
        return [config["metrics"]["sa"]]


class RotDOscillator(Component):
    outputs = {}

    INPUT_CLASS = TraceRotDContainer

    def calculate(self):
        logging.info("** Calculating RotDOscillator")
        iper = self.parameters["periods"]
        idamp = self.parameters["damping"]
        all_oscillators = []
        for per, damp in itertools.product(iper, idamp):
            oscillator_list = []
            for trace_data in self.parent.output.trace_matrix:
                temp_trace = Trace(trace_data, self.parent.output.stats)
                sa_results = new_and_improved_calculate_spectrals(
                    temp_trace, period=per, damping=damp
                )
                acc_sa = sa_results[0]
                acc_sa *= GAL_TO_PCTG
                oscillator_list.append(acc_sa)
            all_oscillators.append(
                RotDOscillatorContainer(
                    period=per,
                    damping=damp,
                    oscillator_dt=sa_results[4],
                    oscillator_matrix=np.stack(oscillator_list),
                )
            )
        self.output = RotDOscillatorCollection(all_oscillators)

    @staticmethod
    def get_parameters(config):
        return [config["metrics"]["sa"]]


class RotateRotD(Component):
    outputs = {}

    def calculate(self):
        logging.info("** Calculating RotateRotD")
        # rotd matrix has dimensions (m, n), where m is the number rotation angles, n
        # is the number of points in the trace.
        rotd_matrix = self._rotate(
            self.parent.output.traces[0].data, self.parent.output.traces[1].data
        )
        self.output = TraceRotDContainer(
            trace_matrix=rotd_matrix,
            stats=self.parent.output.traces[0].stats,
        )

    @staticmethod
    def _rotate(trace1, trace2):
        max_deg = 180
        delta_deg = 1.0
        num_rows = int(max_deg * (1.0 / delta_deg) + 1)
        degrees = np.deg2rad(np.linspace(0, max_deg, num_rows)).reshape((-1, 1))
        cos_deg = np.cos(degrees)
        sin_deg = np.sin(degrees)
        td1 = np.reshape(trace1, (1, -1))
        td2 = np.reshape(trace2, (1, -1))
        rotd_matrix = td1 * cos_deg + td2 * sin_deg
        return rotd_matrix


class TraceMax(Component):
    outputs = {}

    def calculate(self):
        logging.info("** Calculating TraceMax")
        max_list = []
        for trace in self.parent.output.traces:
            max_list.append(
                ReferenceValue(np.max(np.abs(trace.data)), stats=trace.stats)
            )
        self.output = ScalarContainer(max_list)


class CombineMax(Component):
    outputs = {}

    def calculate(self):
        logging.info("** Calculating CombineMax")
        result = np.max([trace.value for trace in self.parent.output.traces])
        self.output = CombinedScalarContainer(
            ReferenceValue(result, self.parent.output.traces[0].stats)
        )


class CombineGeometricMean(Component):
    outputs = {}

    def calculate(self):
        logging.info("** Calculating CombineMax")
        values = [trace.value for trace in self.parent.output.traces]
        geo_mean = np.exp(np.sum(np.log(values) / len(values)))
        self.output = CombinedScalarContainer(
            ReferenceValue(geo_mean, self.parent.output.traces[0].stats)
        )
