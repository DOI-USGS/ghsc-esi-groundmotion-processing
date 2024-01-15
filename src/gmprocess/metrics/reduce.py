"""Module for holding reduction metric processing step classes."""

import numpy as np

from gmprocess.metrics.metric_component_base import Component
from gmprocess.metrics import containers


class TraceMax(Component):
    """Return the maximum absolute value for each trace."""

    outputs = {}
    INPUT_CLASS = containers.Trace

    def calculate(self):
        max_list = []
        for trace in self.parent.output.traces:
            max_list.append(
                containers.ReferenceValue(np.max(np.abs(trace.data)), stats=trace.stats)
            )
        self.output = containers.Scalar(max_list)


class OscillatorMax(Component):
    """Return the maximum absolute value for each trace."""

    outputs = {}
    INPUT_CLASS = containers.OscillatorCollection

    def calculate(self):
        # Loop over each set of oscillator parameters (e.g., period, damping)
        sa_list = []
        for oscillator in self.parent.output.oscillators:
            # Loop over each record
            max_list = []
            for osc in oscillator.oscillators:
                max_list.append(np.max(np.abs(osc)))
            sa_list.append(
                containers.SpectralAcceleration(
                    max_list, stats_list=oscillator.stats_list
                )
            )
        self.output = containers.SpecAccCollection(sa_list)


class RotDMax(Component):
    """Return the maximum absolute value of the oscillators."""

    outputs = {}
    INPUT_CLASS = containers.RotDOscillatorCollection

    def calculate(self):
        rotd_max_list = []
        for oscillator in self.parent.output.oscillators:
            # oscillator is a RotDOscillator container
            abs_matrix = np.abs(oscillator.oscillator_matrix)
            max_array = np.max(abs_matrix, axis=1)
            rotd_max_list.append(
                containers.RotDMax(
                    period=oscillator.period,
                    damping=oscillator.damping,
                    percentile=oscillator.percentile,
                    oscillator_maxes=max_array,
                )
            )
        self.output = containers.RotDMaxCollection(rotd_max_list)


class RotDPercentile(Component):
    """Return the percentile of the oscillator maxes."""

    outputs = {}
    INPUT_CLASS = containers.RotDMaxCollection

    def calculate(self):
        rotd_list = []
        for oscillator in self.parent.output.oscillators:
            # oscillator is a RotDMax container
            rotd_list.append(
                containers.RotD(
                    period=oscillator.period,
                    damping=oscillator.damping,
                    percentile=oscillator.percentile,
                    value=np.percentile(
                        oscillator.oscillator_maxes, oscillator.percentile
                    ),
                )
            )
        self.output = containers.RotDCollection(rotd_list)
