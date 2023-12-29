"""Module for holcing the processing component base class."""

from abc import ABC, abstractmethod
import json
import copy


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
