"""Module for calculating waveform metrics.

# WaveformMetricCalculator
This is the primary class for calculating the metrics for an input stream.

# Component
This is a base class for methods like transforms, reductions, rotations, combinations.
- Component child classes have attributes "parent" and "output".
- The "parent" attribute holds the Component child class for the previous processing
  step.
- The "output" attribute holds a dataclass, such as Container.Trace, or
  Container.Scalar.
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
from gmprocess.metrics.metric_component_base import Component
from gmprocess.metrics import containers

from gmprocess.metrics import combine  # noqa pylint: disable=unused-import
from gmprocess.metrics import reduce  # noqa pylint: disable=unused-import
from gmprocess.metrics import rotate  # noqa pylint: disable=unused-import
from gmprocess.metrics import transform  # noqa pylint: disable=unused-import


class WaveformMetricCalculator:
    """Class for calculating waveform metrics"""

    def __init__(self, stream, steps, config):
        """WaveformMetricCalculator initializer.

        Args:
            stream (StationStream):
                A StationStream object.
            steps (dict):
                A dictionary, in which the key are the name of the metric and the value
                of that key is a list of steps.
            config (dict):
                Config options.
        """
        self.stream = stream
        self.steps = steps
        self.config = config
        self.metric_dict = None

        self.input_data = InputDataComponent(
            containers.Trace(
                [stream.select(channel="HN1")[0], stream.select(channel="HN2")[0]]
            )
        )

    def calculate(self):
        """Calculate waveform metrics."""
        result = self.input_data
        self.metric_dict = {}

        for metric, metric_steps in self.steps.items():
            result = self.input_data
            for metric_step in metric_steps:
                step_module_name, step_class_name = metric_step.split(".")
                step_module = globals()[step_module_name]
                step_class = getattr(step_module, step_class_name)
                parameter_list = step_class.get_parameters(self.config)
                self.validate_params(parameter_list)
                for params in parameter_list:
                    result = step_class(result, params)
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


class InputDataComponent(Component):
    """Class for holding waveform metric input data."""

    outputs = {}

    def __init__(self, input_data):
        super().__init__(None)
        self.output = input_data

    def calculate(self):
        self.output = self.parent
