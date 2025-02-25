"""Module for storing and organizing waveform metrics"""

import sys
import logging
import re
from io import BytesIO

from gmprocess.io.asdf.path_utils import get_stream_path
from gmprocess.io.asdf.stream_workspace import array_to_str
from gmprocess.io.asdf.waveform_metrics_xml import WaveformMetricsXML
from gmprocess.metrics.metric_collection_base import MetricCollection
from gmprocess.metrics.waveform_metric_calculator import WaveformMetricCalculator
from obspy import read_inventory


class WaveformMetricCollection(MetricCollection):
    """WaveformMetricCollection class

    This is a class that is intended to hold a collection of WaveformMetric objects,
    one for each StationStream.

    The class includes the following key attributes:
        - waveform_metrics: a list of WaveformMetricList instances.
        - stream_metadata: a list of dictionaries with keys for important metadata that
          is not stored in a WaveformMetric object.
        - stream_paths: a list of "stream paths" associated with each
          WaveformMetricList; this just convenience information to make bookkeeping
          simpler.

    This default initialization method takes in StreamWorkspace object, but does not
    actually populate the "waveform_metrics" list. It can be populated with the
    "from_streams" or "from_workspace" methods.

    The "from_streams" class method initializes from a list of StationStreams, and
    computes the waveform metrics with the WaveformMetricCalculator class, while the
    "from_workspace" method loads the pre-computed metrics from the StreamWorkspace
    file.
    """

    def __init__(self):
        """Constructor for WaveformMetricCollection object."""

        self.waveform_metrics = []
        self.stream_metadata = []
        self.stream_paths = []

    @classmethod
    def from_streams(cls, streams, event, config, label="default"):
        """Construct the WaveformMetricCollection from a list of StationStreams.

        Args:
            streams (list):
                List of StationStream objects.
            event (gmprocess.utils.scalar_event.ScalarEvent):
                A ScalarEvent object.
            config (dict):
                Dictionary of config options.
            label (str):
                Processing label.
        """

        wmc = cls()
        wmc.calculate_metrics(streams, event, config, label)
        return wmc

    @classmethod
    def from_workspace(cls, workspace, label="default"):
        """Construct the WaveformMetricCollection from a StreamWorkspace file.

        Args:
            workspace (StreamWorkspace):
                A StreamWorkspace object.
            label (str):
                Processing label.
        """
        wmc = cls()
        wmc.get_metrics_from_workspace(workspace, label)
        wmc.get_stream_metadata_from_workspace(workspace)
        return wmc

    def __repr__(self):
        n_stations = len(self.waveform_metrics)
        return f"WaveformMetricCollection: {n_stations} stations"

    def append(self, metric):
        """Append to a WaveformMetricCollection.

        Args:
            metric (WaveformMetricCollection)
                Metric collection to append.
        """
        if not isinstance(metric, WaveformMetricCollection):
            raise ValueError("Appending metric must be a WaveformMetricCollection.")
        self.waveform_metrics.extend(metric.waveform_metrics)
        self.stream_metadata.extend(metric.stream_metadata)
        self.stream_paths.extend(metric.stream_paths)

    def get_metrics_from_workspace(self, workspace, label="default"):
        """Method for populating waveform_metrics from the workspace file.

        Args:
            workspace (StreamWorkspace):
                StreamWorkspace object.
            label (str):
                Processing label; only used if there is more than one processing label
                in the workspace file.
        """

        if "WaveFormMetrics" not in workspace.dataset.auxiliary_data:
            logging.info("WaveFormMetrics not in auxiliary data.")
            return

        for metric in workspace.dataset.auxiliary_data.WaveFormMetrics:
            metric_list = metric.list()
            for met in metric_list:
                met_label = met.split("_")[-1]
                if met_label == label:
                    stream_path = met
                    metric_data = array_to_str(metric[stream_path].data)
                    self.waveform_metrics.append(
                        WaveformMetricsXML.from_xml(metric_data)
                    )
                    self.stream_paths.append(stream_path)

    def calculate_metrics(self, streams, event, config, label="default"):
        """Calculate waveform metrics from a list of streams.

        Args:
            streams (list):
                List of StationStream objects.
            event (gmprocess.utils.scalar_event.ScalarEvent):
                A ScalarEvent object.
            config (dict):
                Dictionary of config options.
            label (str):
                Processing label.
        """
        event_id = event.id.replace("smi:local/", "")
        tag = f"{event_id}_{label}"
        # Need to have something build 'steps'
        for stream in streams:
            if stream.passed:
                wmc = WaveformMetricCalculator(stream, config, event)
                wml = wmc.calculate()
                self.waveform_metrics.append(wml)
                self.stream_paths.append(get_stream_path(stream, tag, config))

    def get_stream_metadata_from_workspace(self, workspace):
        """Lightweight summary info of streams.

        Args:
            workspace (StreamWorkspace):
                StreamWorkspace object.
        """

        if not self.waveform_metrics:
            logging.info("No waveform metrics exist.")
            return

        h5 = workspace.dataset._ASDFDataSet__file

        for stream_path in self.stream_paths:
            net, sta, loc, chan, eid, label = self.unpack_stream_path(stream_path)
            net_sta = f"{net}.{sta}"
            tag = f"{eid}_{label}"
            stream_group = h5["Waveforms"][net_sta]

            # Get a list of stream names and the filter out the ones we don't want
            all_stream_names = list(stream_group.keys())
            stream_names = [
                sn
                for sn in all_stream_names
                if sn.endswith(tag) and sn.startswith(f"{net_sta}.{loc}.{chan}")
            ]

            inventory = read_inventory(
                BytesIO(stream_group["StationXML"][:]), format="stationxml"
            )

            if len(inventory.networks) > 1:
                raise ValueError("More than 1 network found for waveform.")

            if inventory.sender is not None and inventory.sender != inventory.source:
                source = f"{inventory.source},{inventory.sender}"
            else:
                source = inventory.source

            # Sort out sampling rate
            sampling_rate = None
            for inet in inventory.networks:
                if (inet.code != net) or (sampling_rate is not None):
                    break
                for ista in inet.stations:
                    if (ista.code != sta) or (sampling_rate is not None):
                        break
                    for ichan in ista:
                        if ichan.code[0:2] == chan[0:2]:
                            sampling_rate = ichan.sample_rate
                            break

            tr_info = []
            for stream_name in stream_names:
                trace_chan = re.split("[._]", stream_name)[3]
                tag = f"{eid}_{label}"
                trace_path = "_".join([".".join([net_sta, loc, trace_chan]), tag])
                tr_dict = {
                    "network": net,
                    "station": sta,
                    "channel": trace_chan,
                    "location": loc,
                    "passed": True,  # will be updated later if false
                    "tag": tag,
                    "sampling_rate": sampling_rate,
                    "station_name": inventory.networks[0].stations[0].site.name,
                    "latitude": inventory.networks[0].stations[0].latitude,
                    "longitude": inventory.networks[0].stations[0].longitude,
                    "elevation": inventory.networks[0].stations[0].elevation,
                    "source": source,
                }

                # get the provenance information and find corner frequencies
                prov_records = workspace.get_provenance_records(trace_path)
                for record in prov_records:
                    sptype = record.identifier.localpart.split("_")[1]
                    if sptype == "lp":
                        for attr_key, attr_val in record.attributes:
                            if "seis_prov:corner_frequency" in str(attr_key):
                                cur_val = tr_dict.get("lowpass_filter") or sys.float_info.max
                                tr_dict["lowpass_filter"] = min(attr_val, cur_val)
                    elif sptype == "hp":
                        for attr_key, attr_val in record.attributes:
                            if "seis_prov:corner_frequency" in str(attr_key):
                                cur_val = tr_dict.get("highpass_filter") or 0.0
                                tr_dict["highpass_filter"] = max(attr_val, cur_val)
                    elif sptype == "bp":
                        for attr_key, attr_val in record.attributes:
                            if "seis_prov:upper_corner_frequency" in str(attr_key):
                                cur_val = tr_dict.get("lowpass_filter") or sys.float_info.max
                                tr_dict["lowpass_filter"] = min(attr_val, cur_val)
                            if "seis_prov:lower_corner_frequency" in str(attr_key):
                                cur_val = tr_dict.get("highpass_filter") or 0.0
                                tr_dict["highpass_filter"] = max(attr_val, cur_val)

                # get the trace processing parameters, check for failures
                trace_dict = workspace.get_trace_processing_parameters(
                    net_sta, trace_path
                )
                for key, _ in trace_dict.items():
                    if key == "failure":
                        tr_dict["passed"] = False

                sup_stats = workspace.get_supplemental_stats(net_sta, stream_path)
                tr_dict.update(sup_stats)
                tr_info.append(tr_dict)
            self.stream_metadata.append(tr_info)
