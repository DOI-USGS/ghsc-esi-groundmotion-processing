"""Module for the WaveormMetricList class."""

import re
import json

import pandas as pd

from gmprocess.metrics.waveform_metric_type import WaveformMetricType
import gmprocess.metrics.waveform_metric_component as wm_comp
from gmprocess.utils import constants

FLOAT_MATCH = r"[0-9]*\.[0-9]*"
SA_DEFAULT_DAMPING = 5.0
FAS_DEFAULT_SMOOTHING = 20.0
FAS_DEFAULT_METHOD = "Konno-Omachi"

COMP_CLASS = {
    "channels": wm_comp.Channels,
    "geometric_mean": wm_comp.GeometricMean,
    "quadratic_mean": wm_comp.QuadraticMean,
    "rotd": wm_comp.RotD,
}


class WaveformMetricList(object):
    """A class for holding a list of WaveformMetric instances."""

    def __init__(self, metric_list):
        if not all(isinstance(wm, WaveformMetricType) for wm in metric_list):
            raise TypeError("All elements of metric_list must be a WaveformMetric.")
        self.metric_list = metric_list

    def __repr__(self):
        wmstring = ""
        n_metrics = len(self.metric_list)
        wmstring += f"{n_metrics} metric(s) in list:\n"
        if n_metrics <= 5:
            for m in self.metric_list:
                wmstring += f"  {m}\n"
        else:
            for m in self.metric_list[0:2]:
                wmstring += f"  {m}\n"
            wmstring += "  ...\n"
            for m in self.metric_list[-1:]:
                wmstring += f"  {m}\n"
        return wmstring

    def len(self):
        """Number of metrics in list."""
        return len(self.metric_list)

    def to_df(self):
        """Output the WaveformMetricList in a pandas dataframe format."""
        values = []
        imcs = []
        imts = []
        for metric in self.metric_list:
            mdict = metric.to_dict()
            format_imt = mdict["type"].upper()
            if format_imt in ["SA", "FAS"]:
                format_imt += f"({mdict['metric_attributes']['period']:.3f})"
            elif format_imt == "DURATION":
                format_imt += f"({mdict['metric_attributes']['interval']})"

            for comp, val in zip(mdict["components"], mdict["values"]):
                values.append(val)
                imcs.append(comp)
                imts.append(format_imt)

        dataframe = pd.DataFrame(
            {
                "IMC": imcs,
                "IMT": imts,
                "Result": values,
            }
        )
        return dataframe

    @classmethod
    def from_waveform_metric_calculator(cls, wmc):
        """Construct a WaveformMetricList object from a pandas dataframe.

        Args:
            wmc (WaveformMetricsCalculator):
                A WaveformMetricsCalculator object.
        """
        imc_imt_list = list(wmc.steps.keys())
        all_imts = list(set([imt_imt.split("-")[1] for imt_imt in imc_imt_list]))
        metric_list = []
        for imt in all_imts:
            print(f"\n\n### imt: {imt}")
            units = constants.UNITS[imt]

            # Need to get the unique set of metric parameters for this IMT

            # Collect entries for all imcs for this imt and unique set of parameters.
            all_attr_dicts = []
            for mkey, mdl in wmc.metric_dicts.items():
                timc, timt = mkey.split("-")
                if timt == imt:
                    for md in mdl:
                        all_attr_dicts.append(json.dumps(md["parameters"]))
            unique_pars = list(set(all_attr_dicts))

            for unique_par in unique_pars:
                # Collect entries for all imcs for this imt and unique set of
                # parameters.
                all_metric_dicts = []
                all_attr_dicts = []
                for mkey, mdl in wmc.metric_dicts.items():
                    timc, timt = mkey.split("-")
                    if timt == imt:
                        # append the imc to the mdl dicts so that we have it for later.
                        for md in mdl:
                            tunique_par = json.dumps(md["parameters"])
                            if tunique_par == unique_par:
                                md["component"] = timc
                                all_metric_dicts.append(md)

                imc_list = []
                val_list = []
                for metric_dicts in all_metric_dicts:
                    print(f"### len(metric_dicts): {len(metric_dicts)}")
                    for metric_dict in metric_dicts:
                        component_str = metric_dict["component"]
                        print(f"### component_str: {component_str}")
                        component_class = COMP_CLASS[component_str]
                        metric_attributes = metric_dict["parameters"]
                        # Need to check if the result includes an array (e.g., for channels)
                        # or if it is scalar.
                        output = metric_dict["result"].output
                        if hasattr(output, "values"):
                            print("### hasattr(output, 'values')")
                            results = output.values
                            for result in results:
                                # This is hacky... but the only time that 'output' has the
                                # 'values' attribute is for Channels, in which case the
                                # trace channel is a n argument.
                                imc_list.append(
                                    component_class(result.stats["channel"])
                                )
                                val_list.append(result.value)
                        else:
                            print("### hasattr(output, 'value')")
                            result = output.value
                            # This is hacky... but we need to sort out that the RotD class
                            # needs the percentile. Hopefully we can update this in the
                            # future with a better design.
                            if component_str == "rotd":
                                imc_list.append(
                                    component_class(metric_attributes["percentiles"])
                                )
                            else:
                                imc_list.append(component_class())
                            val_list.append(result.value)

                mdict = {
                    "values": val_list,
                    "components": imc_list,
                    "type": imt,
                    "format_type": "",
                    "units": units,
                    "metric_attributes": metric_attributes,
                }
                breakpoint()
                wm = WaveformMetricType.metric_from_dict(mdict)
                metric_list.append(wm)
        return cls(metric_list)

    @classmethod
    def from_df(cls, dataframe, component_to_channel=None):
        """Construct a WaveformMetricList object from a pandas dataframe.

        Args:
            dataframe (str):
                The pandas dataframe created by the MetricsController.
            component_to_channel (dict):
                Optional dictionary mapping the simplified component names to the
                as-recorded channel names.
        """
        imtlist = dataframe["IMT"].unique().tolist()
        metric_list = []
        for imt in imtlist:
            temp_df = dataframe.loc[dataframe["IMT"] == imt]
            imt = imt.lower()
            if imt.startswith("sa"):
                metric_attributes = {
                    "period": float(re.search(FLOAT_MATCH, imt).group()),
                    "damping": SA_DEFAULT_DAMPING,
                }
                fixed_imt = "SA"
            elif imt.startswith("fas"):
                metric_attributes = {
                    "period": float(re.search(FLOAT_MATCH, imt).group()),
                    "method": FAS_DEFAULT_METHOD,
                    "smoothing": FAS_DEFAULT_SMOOTHING,
                }
                fixed_imt = "FAS"
            elif imt.startswith("duration"):
                metric_attributes = {
                    "interval": imt.replace("duration", ""),
                }
                fixed_imt = "Duration"
            elif imt.startswith("cav"):
                metric_attributes = {}
                fixed_imt = "CAV"
            elif imt.startswith("arias"):
                metric_attributes = {}
                fixed_imt = "AriasIntensity"
            elif imt.startswith("sorted"):
                metric_attributes = {}
                fixed_imt = "SortedDuration"
            else:
                metric_attributes = {}
                fixed_imt = imt.upper()
            units = constants.UNITS[fixed_imt.lower()]
            vals = []
            comps = []
            for imc, val in zip(temp_df["IMC"], temp_df["Result"]):
                comps.append(imc)
                vals.append(val)
            mdict = {
                "values": vals,
                "components": comps,
                "type": fixed_imt,
                "format_type": "",
                "units": units,
                "metric_attributes": metric_attributes,
                "component_to_channel": component_to_channel,
            }
            wm = WaveformMetricType.metric_from_dict(mdict)
            metric_list.append(wm)
        return cls(metric_list)
