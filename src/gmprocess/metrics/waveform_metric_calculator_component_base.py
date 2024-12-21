"""Module for holcing the processing component base class."""

from abc import ABC, abstractmethod
import json
import copy

from gmprocess.metrics.waveform_metric_component import Channels
from gmprocess.metrics.utils import component_to_channel


class BaseComponent(ABC):
    """Abstract base class for processing components."""

    def __init__(self, input_data, parameters=None, imc_parameters=None):
        """Initialize a Component.

        Args:
            input_data (Component):
                A Component object of the previous step (or None if there is not
                previous step).
            parameters (dict):
                Dictionary of processing parameters required by the Component.
            imc_parameters (dict):
                Dictionary of imc parameters
        """
        self.prior_step = input_data
        self._validate()
        self.parameters = parameters
        self.imc_parameters = imc_parameters
        # - we need to define a key for self.outputs, which is unique for a given
        #   input_data object as well as any processing parameters for the current
        #   calculation.
        # - think of this as a table lookup (the table is self.outputs) and the table
        #   is unique for each sequence of steps (e.g., ["Integrate", "TraceMax"]).
        param_str = json.dumps(self.parameters)
        imc_param_str = json.dumps(self.imc_parameters)
        output_key = (
            str(id(self.prior_step)) + str(hash(param_str)) + str(hash(imc_param_str))
        )
        if output_key in self.outputs:  # pylint:disable=no-member
            # Note that self.output is a list of Component objects.
            # pylint:disable-next=no-member
            self.output = copy.copy(self.outputs[output_key].output)
            # self.calculate()
            # self.outputs[output_key] = self.output
        else:
            self.calculate()
            self.outputs[output_key] = self  # pylint:disable=no-member

    def _validate(self):
        if self.prior_step is not None:
            # Need to use `type` and not `isinstance` because isinstance treats all
            # child classes as equal.
            # pylint:disable-next=unidiomatic-typecheck, no-member
            if type(self.prior_step.output) not in self.INPUT_CLASS:
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

    def get_component_results(self):
        """Get the scalar(s) and component(s) of the output.

        Metrics that do not reduce to a scalar will not implement
        this method and will throw an exception.
        """
        raise NotImplementedError("This class does not implement get_component_results")

    @staticmethod
    def get_component_parameters(config):
        """Populate a list of params for a metric IMC.

        This needs to be a list of dictionaries.

        The default is a list with an empty dictionary because not all child classes
        need parameters.

        Args:
            config (dict):
                Config dictionary.
        """
        return {}

    @staticmethod
    def get_type_parameters(config):
        """Populate a list of params for a metric Component.

        This needs to be a list of dictionaries.

        The default is a list with an empty dictionary because not all child classes
        need parameters.

        Args:
            config (dict):
                Config dictionary.
        """
        return {}

    @classmethod
    def clear_children(cls):
        for sub_cls in cls.__subclasses__():
            sub_cls.outputs = {}


def get_channel_outputs(mbc):
    """Returns a tuple of two lists: the scalar outputs and the channel
    objects of the input waveform base class."""
    vals = []
    coms = []
    channels = [val.stats["channel"] for val in mbc.output.values]
    _, chan2comp = component_to_channel(channels)
    for trace in mbc.output.values:
        vals.append(trace.value)
        coms.append(
            str(Channels(trace.stats["channel"], chan2comp[trace.stats["channel"]]))
        )
    return (vals, coms)


def get_component_output(mbc, comp):
    """Returns a tuple of two lists: the scalar output and the component
    object of the input waveform base class."""
    return ([mbc.output.value.value], [comp])
