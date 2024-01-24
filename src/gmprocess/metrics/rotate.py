"""Module for holding classes for rotation metric processing steps."""

import numpy as np

from gmprocess.metrics.waveform_metric_calculator_component_base import BaseComponent
from gmprocess.metrics import containers


class RotD(BaseComponent):
    """Class for doing the RotD rotation."""

    outputs = {}
    INPUT_CLASS = [containers.Trace]

    def calculate(self):
        # rotd matrix has dimensions (m, n), where m is the number rotation angles, n
        # is the number of points in the trace.
        rotd_matrix = self._rotate(
            self.prior_step.output.traces[0].data, self.prior_step.output.traces[1].data
        )
        self.output = containers.RotDTrace(
            matrix=rotd_matrix,
            stats=self.prior_step.output.traces[0].stats,
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
