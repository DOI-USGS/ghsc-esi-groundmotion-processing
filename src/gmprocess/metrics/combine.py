"""Module for holding classes for combining traces."""

import numpy as np

from gmprocess.metrics.metric_component_base import Component
from gmprocess.metrics import containers


class GeometricMean(Component):
    """Return the geometric mean across multiple traces."""

    outputs = {}
    INPUT_CLASS = containers.Scalar

    def calculate(self):
        values = [trace.value for trace in self.parent.output.traces]
        geo_mean = np.exp(np.sum(np.log(values) / len(values)))
        self.output = containers.CombinedScalar(
            containers.ReferenceValue(geo_mean, self.parent.output.traces[0].stats)
        )


class SpectraQuadraticMean(Component):
    """Return the quadratic mean of the Fourier spectra across multiple traces."""

    outputs = {}
    INPUT_CLASS = containers.FourierSpectra

    def calculate(self):
        fas_matrix = np.stack(self.parent.output.fourier_spectra)
        nrow = fas_matrix.shape[0]
        quad_mean = np.sqrt(np.sum(fas_matrix**2, axis=0) / nrow)
        self.output = containers.CombinedSpectra(
            frequency=self.parent.output.frequency,
            fourier_spectra=quad_mean,
        )
