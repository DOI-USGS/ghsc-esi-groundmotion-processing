"""Module for holding reduction metric processing step classes."""

import numpy as np

from gmprocess.metrics.metric_component_base import Component
from gmprocess.metrics import containers
from gmprocess.utils.constants import GAL_TO_PCTG


class TraceMax(Component):
    """Return the maximum absolute value for each trace."""

    outputs = {}
    INPUT_CLASS = containers.Trace

    def calculate(self):
        max_list = []
        for trace in self.prior_step.output.traces:
            max_list.append(
                containers.ReferenceValue(np.max(np.abs(trace.data)), stats=trace.stats)
            )
        self.output = containers.Scalar(max_list)


class Duration(Component):
    """Return the duration from the Arias intensity."""

    outputs = {}
    INPUT_CLASS = containers.Trace

    def calculate(self):
        duration_list = []
        interval_str = self.parameters["intervals"].split("-")
        interval = [float(istr) / 100 for istr in interval_str]
        for trace in self.prior_step.output.traces:
            times = np.arange(trace.stats.npts) / trace.stats.sampling_rate
            # Normalized Aarias Intensity
            arias_norm = trace.data / np.max(trace.data)
            ind0 = np.argmin(np.abs(arias_norm - interval[0]))
            ind1 = np.argmin(np.abs(arias_norm - interval[1]))
            dur = times[ind1] - times[ind0]
            duration_list.append(containers.ReferenceValue(dur, stats=trace.stats))
        self.output = containers.Scalar(duration_list)

    @staticmethod
    def get_parameters(config):
        return config["metrics"]["duration"]


class CAV(Component):
    """Compute the cumulative absolute velocity."""

    outputs = {}
    INPUT_CLASS = containers.Trace

    def calculate(self):
        cav_list = []
        for trace in self.prior_step.output.traces:
            new_trace = trace.copy()
            # Convert from cm/s/s to m/s/s
            new_trace.data *= 0.01
            # Convert from m/s/s to g-s
            new_trace.data *= GAL_TO_PCTG
            # Absolute value
            np.abs(new_trace.data, out=new_trace.data)
            # Integrate, and force time domain to avoid frequency-domain artifacts that
            # creat negative values.
            new_trace.integrate(frequency=False)
            cav = np.max(new_trace.data)
            cav_list.append(containers.ReferenceValue(cav, stats=trace.stats))
        self.output = containers.Scalar(cav_list)


class OscillatorMax(Component):
    """Return the maximum absolute value for each oscillator."""

    outputs = {}
    INPUT_CLASS = containers.Oscillator

    def calculate(self):
        # Loop over each record
        max_list = []
        for osc, stats in zip(
            self.prior_step.output.oscillators, self.prior_step.output.stats_list
        ):
            max_list.append(
                containers.ReferenceValue(value=np.max(np.abs(osc)), stats=stats)
            )
        self.output = containers.Scalar(max_list)


class RotDMax(Component):
    """Return the maximum absolute value of the oscillators."""

    outputs = {}
    INPUT_CLASS = containers.RotDOscillator

    def calculate(self):
        abs_matrix = np.abs(self.prior_step.output.oscillator_matrix)
        max_array = np.max(abs_matrix, axis=1)
        self.output = containers.RotDMax(
            period=self.prior_step.output.period,
            damping=self.prior_step.output.damping,
            percentile=self.prior_step.output.percentile,
            oscillator_maxes=max_array,
            stats=self.prior_step.output.stats,
        )


class RotDPercentile(Component):
    """Return the percentile of the oscillator maxes."""

    outputs = {}
    INPUT_CLASS = containers.RotDMax

    def calculate(self):
        result = np.percentile(
            self.prior_step.output.oscillator_maxes,
            self.prior_step.output.percentile,
        )
        self.output = containers.RotD(
            period=self.prior_step.output.period,
            damping=self.prior_step.output.damping,
            percentile=self.prior_step.output.percentile,
            value=containers.ReferenceValue(result, stats=self.prior_step.output.stats),
        )
