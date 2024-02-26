"""Module for holding classes for combining traces."""

import numpy as np

from gmprocess.metrics.waveform_metric_calculator_component_base import (
    BaseComponent,
    get_component_output,
)
from gmprocess.metrics import containers
import gmprocess.metrics.waveform_metric_component as wm_comp


class ArithmeticMean(BaseComponent):
    """Return the arithmetic mean across multiple traces."""

    outputs = {}
    INPUT_CLASS = [containers.Scalar]

    def calculate(self):
        values = [trace.value for trace in self.prior_step.output.values]
        amean = np.mean(values)
        self.output = containers.CombinedScalar(
            containers.ReferenceValue(amean, self.prior_step.output.values[0].stats)
        )

    def get_component_results(self):
        return get_component_output(self, str(wm_comp.ArithmeticMean()))


class GeometricMean(BaseComponent):
    """Return the geometric mean across multiple traces."""

    outputs = {}
    INPUT_CLASS = [containers.Scalar]

    def calculate(self):
        values = [trace.value for trace in self.prior_step.output.values]
        geo_mean = np.exp(np.sum(np.log(values) / len(values)))
        self.output = containers.CombinedScalar(
            containers.ReferenceValue(geo_mean, self.prior_step.output.values[0].stats)
        )

    def get_component_results(self):
        return get_component_output(self, str(wm_comp.GeometricMean()))


class SpectraQuadraticMean(BaseComponent):
    """Return the quadratic mean of the Fourier spectra across multiple traces."""

    outputs = {}
    INPUT_CLASS = [containers.FourierSpectra]

    def calculate(self):
        fas_matrix = np.stack(self.prior_step.output.fourier_spectra)
        nrow = fas_matrix.shape[0]
        quad_mean = np.sqrt(np.sum(fas_matrix**2, axis=0) / nrow)
        self.output = containers.CombinedSpectra(
            frequency=self.prior_step.output.frequency,
            fourier_spectra=quad_mean,
        )

    def get_component_results(self):
        return get_component_output(self, str(wm_comp.QuadraticMean()))
