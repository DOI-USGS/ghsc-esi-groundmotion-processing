"""Module for the WaveormMetricList class."""

import re

import pandas as pd

from gmprocess.metrics.waveform_metric_type import WaveformMetricType
from gmprocess.utils import constants

FLOAT_MATCH = r"[0-9]*\.[0-9]*"
SA_DEFAULT_DAMPING = 5.0
FAS_DEFAULT_SMOOTHING = 20.0
FAS_DEFAULT_METHOD = "Konno-Omachi"


class WaveformMetricList(object):
    """A class for holding a list of WaveformMetric instances."""

    def __init__(self, metric_list):
        if not all(isinstance(wm, WaveformMetricType) for wm in metric_list):
            raise TypeError("All elements of metric_list must be a WaveformMetric.")
        self.metric_list = metric_list

    def __iter__(self):
        return self.metric_list.__iter__()

    def __getitem__(self, i):
        return self.metric_list[i]

    def len(self):
        return len(self.metric_list)

    def select(self, mtype=None, **kwargs):
        """Return a new WaveformMetricList that meets some criteria.

        Args:
            mtype (str):
                The metric type to select.
            **kwargs:
                Additional criteria to be applied to the metric's 'metric_attributes'.
        """
        selected = []
        for metric in self:
            if mtype is None or metric.type != mtype:
                continue
            att_match = []
            for k, v in kwargs.items():
                if k not in metric.metric_attributes:
                    att_match.append(False)
                    continue
                if metric.metric_attributes[k] != v:
                    att_match.append(False)
                else:
                    att_match.append(True)
            if all(att_match):
                selected.append(metric)
        return WaveformMetricList(selected)

    @property
    def metric_types(self):
        mtypes = []
        for metric in self:
            mtypes.append(metric.type)
        return mtypes

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

    def to_df(self):
        """Output the WaveformMetricList in a pandas dataframe format."""
        values = []
        imcs = []
        imts = []
        for metric in self:
            mdict = metric.to_dict()

            for comp, val in zip(mdict["components"], mdict["values"]):
                values.append(val)
                imcs.append(str(comp))
                imts.append(metric.identifier)

        dataframe = pd.DataFrame(
            {
                "IMC": imcs,
                "IMT": imts,
                "Result": values,
            }
        )
        return dataframe

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
            if imt.startswith("s"):
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
                fixed_imt = "Arias"
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
