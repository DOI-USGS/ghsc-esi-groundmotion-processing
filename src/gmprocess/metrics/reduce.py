"""Module for holding reduction metric processing step classes."""

import numpy as np

from gmprocess.metrics.waveform_metric_calculator_component_base import (
    BaseComponent,
    get_channel_outputs,
)
from gmprocess.metrics import containers
from gmprocess.utils.constants import GAL_TO_PCTG
import gmprocess.metrics.waveform_metric_component as wm_comp


class TraceMax(BaseComponent):
    """Return the maximum absolute value for each trace."""

    outputs = {}
    INPUT_CLASS = [containers.Trace]

    def calculate(self):
        max_list = []
        for trace in self.prior_step.output.traces:
            idx = np.argmax(np.abs(trace.data))
            dtimes = trace.times()
            dtime = dtimes[idx]
            tstats = trace.stats
            tstats["peak_time"] = dtime
            unit_factor = 1.0
            if tstats["standard"]["units_type"] == "acc":
                unit_factor = GAL_TO_PCTG
            max_list.append(
                containers.ReferenceValue(
                    unit_factor * np.abs(trace.data[idx]), stats=tstats
                )
            )
        self.output = containers.Scalar(max_list)

    def get_component_results(self):
        return get_channel_outputs(self)


class Duration(BaseComponent):
    """Return the duration from the Arias intensity."""

    outputs = {}
    INPUT_CLASS = [containers.Trace]

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

    def get_component_results(self):
        return get_channel_outputs(self)

    @staticmethod
    def get_type_parameters(config):
        return config["metrics"]["type_parameters"]["duration"]


class CAV(BaseComponent):
    """Compute the cumulative absolute velocity."""

    outputs = {}
    INPUT_CLASS = [containers.Trace]

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

    def get_component_results(self):
        return get_channel_outputs(self)


class OscillatorMax(BaseComponent):
    """Return the maximum absolute value for each oscillator."""

    outputs = {}
    INPUT_CLASS = [containers.Oscillator]

    def calculate(self):
        # Loop over each record
        max_list = []
        for osc, stats in zip(
            self.prior_step.output.oscillators, self.prior_step.output.stats_list
        ):
            max_list.append(
                containers.ReferenceValue(
                    value=GAL_TO_PCTG * np.max(np.abs(osc)), stats=stats
                )
            )
        self.output = containers.Scalar(max_list)

    def get_component_results(self):
        return get_channel_outputs(self)


class RotDTraceMax(BaseComponent):
    """Return the maximum absolute value of the traces."""

    outputs = {}
    INPUT_CLASS = [containers.RotDTrace]

    def calculate(self):
        abs_matrix = np.abs(self.prior_step.output.matrix)
        max_array = np.max(abs_matrix, axis=1)
        unit_factor = 1.0
        if self.prior_step.output.stats["standard"]["units_type"] == "acc":
            unit_factor = GAL_TO_PCTG
        self.output = containers.RotDMax(
            period=None,
            damping=None,
            oscillator_maxes=unit_factor * max_array,
            stats=self.prior_step.output.stats,
        )


class RotDOscMax(BaseComponent):
    """Return the maximum absolute value of the oscillators."""

    outputs = {}
    INPUT_CLASS = [containers.RotDOscillator]

    def calculate(self):
        abs_matrix = np.abs(self.prior_step.output.matrix)
        max_array = np.max(abs_matrix, axis=1)
        self.output = containers.RotDMax(
            period=self.prior_step.output.period,
            damping=self.prior_step.output.damping,
            oscillator_maxes=GAL_TO_PCTG * max_array,
            stats=self.prior_step.output.stats,
        )


class RotDPercentile(BaseComponent):
    """Return the percentile of the oscillator maxes."""

    outputs = {}
    INPUT_CLASS = [containers.RotDMax]

    def calculate(self):
        percentile = self.imc_parameters["percentiles"]
        result = np.percentile(self.prior_step.output.oscillator_maxes, percentile)
        self.output = containers.RotD(
            period=self.prior_step.output.period,
            damping=self.prior_step.output.damping,
            percentile=percentile,
            value=containers.ReferenceValue(result, stats=self.prior_step.output.stats),
        )

    def get_component_results(self):
        return (
            [self.output.value.value],
            [str(wm_comp.RotD(self.imc_parameters["percentiles"]))],
        )

    @staticmethod
    def get_component_parameters(config):
        return {
            "percentiles": config["metrics"]["component_parameters"]["rotd"][
                "percentiles"
            ],
        }
