"""Module for calculating waveform metrics.

# WaveformMetricCalculator
This is the primary class for calculating the metrics for an input stream.

# Component
This is a base class for methods like transforms, reductions, rotations, combinations.
- Component child classes have attributes "prior_step" and "output".
- The "prior_step" attribute holds the Component child class for the previous processing
  step.
- The "output" attribute holds a dataclass, such as Container.Trace, or
  Container.Scalar.
- All Component class have a "calculate" method that defines the calculations for that
  processing step, places the results in an appropriate dataclass, and places that
  dataclass in the "output" attribute.

# InputDataComponent
This is a special child of Component for holding the input data. Its "prior_step"
attribute is None.

# WaveformMetricCalculator Details
- Initially, "result" holds the InputDataComponent, which is handed off as output
  for the next processing step.
- "metric_dicts" is a dictionary that holds results for all completed steps, in which keys are unique hashes.
- "metric_dicts" can be inspected by looking at the prior_step/output attributes, e.g.

    metric_dicts["test1"]

  is an object with the type of the last step, and the previous step can be accessed
  with

    metric_dicts["test1"].prior_step

  while the data resulting from the step can be accessed with

    metric_dicts["test1"].output

  And the result of the previous step can be accessed with

    metric_dicts["test1"].prior_step.output

  This continues recursively until the "prior_step" attribute is Null, which is the
  initial input data.

  The "outputs" attribute is a shared dictionary across all steps that caches the
  and are re-used

"""

import json
import itertools


from gmprocess.metrics.waveform_metric_list import WaveformMetricList
from gmprocess.metrics.waveform_metric_type import WaveformMetricType
from gmprocess.metrics.waveform_metric_calculator_component_base import BaseComponent
from gmprocess.metrics import containers

from gmprocess.metrics import combine
from gmprocess.metrics import reduce
from gmprocess.metrics import rotate
from gmprocess.metrics import transform
from gmprocess.utils import constants


class WaveformMetricCalculator:
    """Class for calculating waveform metrics"""

    all_steps = {
        "channels-pga": [reduce.TraceMax],
        "channels-pgv": [transform.Integrate, reduce.TraceMax],
        "channels-psa": [
            transform.TraceOscillator,
            reduce.OscillatorPseudoAcceleration,
        ],
        "channels-sa": [transform.TraceOscillator, reduce.OscillatorMaxAcceleration],
        "channels-psv": [transform.TraceOscillator, reduce.OscillatorPseudoVelocity],
        "channels-sv": [transform.TraceOscillator, reduce.OscillatorMaxVelocity],
        "channels-sd": [transform.TraceOscillator, reduce.OscillatorMaxDisplacement],
        "channels-arias": [transform.Arias, reduce.TraceMax],
        "channels-duration": [transform.Arias, reduce.Duration],
        "channels-cav": [reduce.CAV],
        "channels-fas": [transform.FourierAmplitudeSpectra, transform.SmoothSpectra],
        "arithmetic_mean-pga": [reduce.TraceMax, combine.ArithmeticMean],
        "arithmetic_mean-pgv": [
            transform.Integrate,
            reduce.TraceMax,
            combine.ArithmeticMean,
        ],
        "arithmetic_mean-sa": [
            transform.TraceOscillator,
            reduce.OscillatorMaxAcceleration,
            combine.ArithmeticMean,
        ],
        "arithmetic_mean-arias": [
            transform.Arias,
            reduce.TraceMax,
            combine.ArithmeticMean,
        ],
        "arithmetic_mean-duration": [
            transform.Arias,
            reduce.Duration,
            combine.ArithmeticMean,
        ],
        "arithmetic_mean-cav": [
            reduce.CAV,
            combine.ArithmeticMean,
        ],
        "geometric_mean-pga": [reduce.TraceMax, combine.GeometricMean],
        "geometric_mean-pgv": [
            transform.Integrate,
            reduce.TraceMax,
            combine.GeometricMean,
        ],
        "geometric_mean-sa": [
            transform.TraceOscillator,
            reduce.OscillatorMaxAcceleration,
            combine.GeometricMean,
        ],
        "geometric_mean-arias": [
            transform.Arias,
            reduce.TraceMax,
            combine.GeometricMean,
        ],
        "geometric_mean-duration": [
            transform.Arias,
            reduce.Duration,
            combine.GeometricMean,
        ],
        "geometric_mean-cav": [
            reduce.CAV,
            combine.GeometricMean,
        ],
        "quadratic_mean-fas": [
            transform.FourierAmplitudeSpectra,
            combine.SpectraQuadraticMean,
            transform.SmoothSpectra,
        ],
        "rotd-pga": [
            rotate.RotD,
            reduce.RotDTraceMax,
            reduce.RotDPercentile,
        ],
        "rotd-pgv": [
            transform.Integrate,
            rotate.RotD,
            reduce.RotDTraceMax,
            reduce.RotDPercentile,
        ],
        "rotd-sa": [
            rotate.RotD,
            transform.RotDOscillator,
            reduce.RotDOscMaxAcceleration,
            reduce.RotDPercentileAcceleration,
        ],
        "rotd-psa": [
            rotate.RotD,
            transform.RotDOscillator,
            reduce.RotDOscPseudoAcceleration,
            reduce.RotDPercentileAcceleration,
        ],
        "rotd-sv": [
            rotate.RotD,
            transform.RotDOscillator,
            reduce.RotDOscMaxVelocity,
            reduce.RotDPercentileVelocity,
        ],
        "rotd-psv": [
            rotate.RotD,
            transform.RotDOscillator,
            reduce.RotDOscPseudoVelocity,
            reduce.RotDPercentileVelocity,
        ],
        "rotd-sd": [
            rotate.RotD,
            transform.RotDOscillator,
            reduce.RotDOscMaxDisplacement,
            reduce.RotDPercentileDisplacement,
        ],
    }

    def __init__(self, stream, config, event=None):
        """WaveformMetricCalculator initializer.

        Args:
            stream (StationStream):
                A StationStream object.
            config (dict):
                The config dictionary.
            event (Event):
                An event object, required for radial-transverse components.
        """
        self.event = event
        self.stream = stream
        self.config = config

        self.steps = {}
        self._set_steps()
        # self.metric_dicts = None
        self.wml = None

        self.input_data = InputDataComponent(containers.Trace(stream.traces))

    @classmethod
    def available_imcs(cls):
        all_imcs = [k.split("-")[0] for k in cls.all_steps.keys()]
        return list(set(all_imcs))

    def calculate(self):
        """Calculate waveform metrics."""

        # self.metric_dicts and the stuff that builds it can be removed if
        # we never think we're going to use it
        # self.metric_dicts = {}
        metric_dict = {}
        # metric is something like "channels-pga", i.e., an imc-imt
        # metric_steps is the list of operations that will produce the
        #   metric, such as "reduce.TraceMax"
        for metric, metric_steps in self.steps.items():
            _, imt = metric.split("-")
            if imt not in metric_dict:
                metric_dict[imt] = {}
            metric_results = [self.input_data]
            for metric_step in metric_steps:
                parameters = metric_step.get_type_parameters(self.config)
                parameter_list = self._flatten_params(parameters)
                comp_parameters = metric_step.get_component_parameters(self.config)
                comp_parameter_list = self._flatten_params(comp_parameters)
                next_step = []
                for prior_step in metric_results:
                    for comp_params in comp_parameter_list:
                        for params in parameter_list:
                            # this is where the metric_step calculation is done (if needed)
                            next_step.append(
                                metric_step(prior_step, params, comp_params)
                            )
                metric_results = next_step
            # self.metric_dicts[metric] = []
            # 'metric_results' list maps to the alternative parameters for 'metric'
            for result in metric_results:
                param_dict = {}
                # imc_param_dict = {}
                result_temp = result
                while not isinstance(result_temp, InputDataComponent):
                    if result_temp.parameters:
                        # assume parameter keys are not re-used.
                        param_dict.update(result_temp.parameters)
                    # if result_temp.imc_parameters:
                    #     imc_param_dict.update(result_temp.imc_parameters)
                    result_temp = result_temp.prior_step
                # self.metric_dicts[metric].append(
                #     {
                #         "result": result,
                #         "parameters": param_dict,
                #         "imc_parameters": imc_param_dict,
                #     }
                # )
                param_key = hash(json.dumps(param_dict))
                if param_key not in metric_dict[imt]:
                    # This fixes a disagreement between functions on whether
                    # the argument should be "period" or "periods"
                    if "periods" in param_dict:
                        param_dict["period"] = param_dict["periods"]
                        del param_dict["periods"]
                    # ditto for intervals vs interval
                    if "intervals" in param_dict:
                        param_dict["interval"] = param_dict["intervals"]
                        del param_dict["intervals"]
                    metric_dict[imt][param_key] = {
                        "values": [],
                        "components": [],
                        "type": imt,
                        "units": constants.UNITS[imt],
                        "format_type": "",
                        "metric_attributes": param_dict,
                    }
                (vals, comps) = result.get_component_results()
                metric_dict[imt][param_key]["values"] += vals
                metric_dict[imt][param_key]["components"] += comps
        metric_list = []
        for dval in metric_dict.values():
            for mdict in dval.values():
                metric_list.append(WaveformMetricType.metric_from_dict(mdict))

        self.wml = WaveformMetricList(metric_list)
        BaseComponent.clear_children()
        return self.wml

    def _flatten_params(self, parameters):
        """Validate that the parameter_list has the correct structure.

        Needs to be a list of dictionaries to ensure the appropriate key is generated
        for Component.outputs.
        """
        non_list_pars = {}
        list_pars = {}
        for par_key, par_val in parameters.items():
            if not isinstance(par_val, list):
                non_list_pars[par_key] = par_val
            else:
                list_pars[par_key] = par_val
        parameter_list = []
        list_par_lists = []
        list_par_names = []
        for k, v in list_pars.items():
            list_par_lists.append(v)
            list_par_names.append(k)
        for flat_pars in itertools.product(*list_par_lists):
            flat_dict = non_list_pars.copy()
            for k, v in zip(list_par_names, flat_pars):
                flat_dict[k] = v
            parameter_list.append(flat_dict)
        return parameter_list

    def _set_steps(self):
        for imc, imt_list in self.config["metrics"]["components_and_types"].items():
            for imt in imt_list:
                step_key = "-".join([imc, imt])
                if step_key not in self.all_steps:
                    raise ValueError(f"The {step_key} metric is not supported.")
                self.steps[step_key] = self.all_steps[step_key]


class InputDataComponent(BaseComponent):
    """Class for holding waveform metric input data."""

    outputs = {}

    def __init__(self, input_data):
        super().__init__(None)
        self.output = input_data

    def calculate(self):
        self.output = self.prior_step
