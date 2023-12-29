"""Module for holding reduction metric processing step classes."""

import numpy as np

from gmprocess.metrics.metric_component_base import Component
from gmprocess.metrics import containers


class TraceMax(Component):
    """Return the maximum absolute value for each trace."""

    outputs = {}

    def calculate(self):
        max_list = []
        for trace in self.parent.output.traces:
            max_list.append(
                containers.ReferenceValue(np.max(np.abs(trace.data)), stats=trace.stats)
            )
        self.output = containers.Scalar(max_list)
