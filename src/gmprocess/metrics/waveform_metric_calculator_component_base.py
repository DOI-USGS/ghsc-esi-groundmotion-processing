"""Module for holcing the processing component base class."""

from abc import ABC, abstractmethod
import json
import copy


class BaseComponent(ABC):
    """Abstract base class for processing components."""

    def __init__(self, input_data, parameters=None):
        """Initialize a Component.

        Args:
            input_data (Component):
                A Component object of the previous step (or None if there is not
                previous step).
            parameters (dict):
                Dictionary of processing parameters required by the Component.
        """
        self.prior_step = input_data
        self._validate()
        self.parameters = parameters
        # - we need to define a key for self.outputs, which is unique for a given
        #   input_data object as well as any processing parameters for the current
        #   calculation.
        # - think of this as a table lookup (the table is self.outputs) and the table
        #   is unique for each sequence of steps (e.g., ["Integrate", "TraceMax"]).
        param_str = json.dumps(self.parameters)
        output_key = str(id(self.prior_step)) + str(hash(param_str))
        if output_key in self.outputs:  # pylint:disable=no-member
            # Note that self.output is a list of Component objects.
            # pylint:disable-next=no-member
            self.output = copy.copy(self.outputs[output_key])
        else:
            self.calculate()
            self.outputs[output_key] = self.output  # pylint:disable=no-member

    def _validate(self):
        if self.prior_step is not None:
            # Need to use `type` and not `isinstance` because isinstance treats all
            # child classes as equal.
            # pylint:disable-next=unidiomatic-typecheck, no-member
            if not type(self.prior_step.output) in self.INPUT_CLASS:
                raise TypeError(
                    f"Incorrect INPUT_CLASS {type(self.prior_step.output)} for "
                    f"{type(self)}"
                )

    def __repr__(self):
        step_list = [type(self).__name__]
        step = self.prior_step
        while step:
            step_list.append(type(step).__name__)
            step = step.prior_step
        step_list.reverse()
        output_str_list = str(self.output).split("\n")
        if len(output_str_list) > 1:
            output_str_list = [output_str_list[0]] + [
                "  " + osl for i, osl in enumerate(output_str_list) if i
            ]
        output_str = "\n".join(output_str_list)
        return (
            f"metric_component_base.Component: {type(self)},\n"
            f"  Component steps: {'.'.join(step_list)}\n"
            f"  .output: {output_str}"
        )

    @abstractmethod
    def calculate(self):
        """Component calculate method.

        All components must define this method, which should set the self.output
        parameter.
        """

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
        return {}
