# stdlib imports
import json
import logging
import pathlib
import re

# third party imports
from gmpacket.feature import (
    Feature,
    FeatureGeometry,
    FeatureProperties,
    Metric,
    MetricDimensions,
    MetricProperties,
    Stream,
    StreamHousing,
    StreamProperties,
    Trace,
    TraceProperties,
)
from gmpacket.packet import Event, GroundMotionPacket
from gmpacket.provenance import (
    OrganizationAgent,
    PersonAgent,
    Provenance,
    SoftwareAgent,
    Website,
)

# local imports
from gmprocess.io.asdf.stream_workspace import StreamWorkspace

METRIC_INFO = {
    "PGA": ("Peak ground acceleration", "%g"),
    "PGV": ("Peak ground velocity", "cm/s"),
    "SA": ("Spectral acceleration", "%g"),
    "DURATION": ("Earthquake duration", "s"),
    "FAS": ("Fourier Amplitude Spectra", "cm/s"),
    "SORTED_DURATION": (
        "Sorted earthquake duration",
        "s",
    ),
    "ARIAS": ("Earthquake arias intensity", "m/s"),
}

VERSION = "0.1dev"
MIN_PGA = 0.0464


class GroundMotionPacketWriter(object):
    def __init__(self, gmpacket_directory, workspace_file, label=None):
        self._workspace = StreamWorkspace.open(workspace_file)
        self._gmpacket_directory = pathlib.Path(gmpacket_directory)
        self._label = label

    def get_gmp_event(self, eventid):
        scalar_event = self._workspace.getEvent(eventid)
        # id, time, magnitude, lat, lon, depth)
        gmp_event = Event.from_params(
            eventid,
            scalar_event.time.datetime,
            scalar_event.magnitude,
            scalar_event.latitude,
            scalar_event.longitude,
            scalar_event.depth_km,
        )
        return gmp_event

    def get_housing(self):
        gmp_housing = StreamHousing(
            cosmos_code=0,
            description="",
            stream_depth=0,
            stream_location="",
        )
        return gmp_housing

    def get_provenance(self, trace):
        provdoc = trace.getProvenanceDocument()
        provdict = json.loads(provdoc.serialize())
        provdict.pop("entity")
        provdict.pop("activity")
        for label, agent in provdict["agent"].items():
            if agent["prov:type"]["$"] == "prov:Person":
                if "seis_prov:role" not in agent:
                    provdict["agent"][label]["seis_prov:role"] = "data processor"
        gmp_provenance = Provenance(**provdict)
        return gmp_provenance

    def get_trace_properties(self, trace, channel, loc, as_recorded):
        gmp_trace_props = TraceProperties(
            channel_code=channel,
            location_code=loc,
            as_recorded=as_recorded,
            azimuth=trace.stats.standard.horizontal_orientation,
            dip=trace.stats.standard.vertical_orientation,
            start_time=trace.stats.starttime.datetime,
            end_time=trace.stats.endtime.datetime,
        )
        return gmp_trace_props

    def get_metrics(self, summary, channel, net, sta):
        array_metrics = {
            "DURATION": DurationMetricHolder(),
            "SA": SAMetricHolder(summary.damping),
            "FAS": FASMetricHolder(),
        }
        gmp_metrics = []
        for metric in summary.imts:
            logging.info(f"Outputting metric {net}.{sta}.{channel}.{metric}")
            data_value = summary.get_pgm(metric, channel)
            if data_value is None:
                continue
            if re.match("DURATION", metric) is not None:
                metric_holder = array_metrics["DURATION"]
                metric_holder.add_value(data_value, metric)
            elif re.match("SA", metric) is not None:
                metric_holder = array_metrics["SA"]
                metric_holder.add_value(data_value, metric)
            elif re.match("FAS", metric) is not None:
                metric_holder = array_metrics["FAS"]
                metric_holder.add_value(data_value, metric)
            else:
                description, units = METRIC_INFO[metric]
                gmp_metprops = MetricProperties(
                    description=description,
                    name=metric,
                    units=units,
                )
                gmp_metric = Metric(properties=gmp_metprops, values=data_value)
                gmp_metrics.append(gmp_metric)
        for metric_type, metric_holder in array_metrics.items():
            dimensions = metric_holder.get_dimensions()
            values = metric_holder.get_values()
            if not len(values) or not len(values[0]):
                continue
            description, units = METRIC_INFO[metric_type]
            gmp_metprops = MetricProperties(
                description=description,
                name=metric_holder.metric_type,
                units=units,
            )
            try:
                gmp_metdims = MetricDimensions(**dimensions)
            except Exception as e:
                x = 1
                gmp_metdims = MetricDimensions(**dimensions)
            gmp_metric = Metric(
                properties=gmp_metprops,
                dimensions=gmp_metdims,
                values=values,
            )
            gmp_metrics.append(gmp_metric)
        return gmp_metrics

    def write(self):
        nevents = 0
        nstreams = 0
        ntraces = 0
        files = []
        for eventid in self._workspace.getEventIds():
            nevents += 1
            gmp_event = self.get_gmp_event(eventid)
            ds = self._workspace.dataset
            gmp_features = []
            gmp_provenance = None
            station_list = ds.waveforms.list()
            for station_id in station_list:
                streams = self._workspace.getStreams(
                    eventid, stations=[station_id], labels=[self._label]
                )
                gmp_streams = []
                for stream in streams:
                    if not stream.passed:
                        continue
                    logging.info(f"Writing stream {stream.id}...")
                    network, station, instrument = stream.get_id().split(".")
                    gmp_housing = self.get_housing()
                    gmp_stream_props = StreamProperties(
                        band_code=instrument[0],
                        instrument_code=instrument[1],
                        samples_per_second=stream.traces[0].stats.sampling_rate,
                        stream_housing=gmp_housing,
                    )

                    nstreams += 1
                    for trace in stream:
                        ntraces += 1
                        if gmp_provenance is None:
                            gmp_provenance = self.get_provenance(trace)
                        net = trace.stats.network
                        sta = trace.stats.station
                        loc = trace.stats.location

                        summary = self._workspace.getStreamMetrics(
                            eventid,
                            net,
                            sta,
                            self._label,
                        )
                        gmp_traces = []
                        for channel in summary.components:
                            gmp_metrics = None
                            as_recorded = True
                            for imc in summary.available_imcs:
                                if channel.lower() in imc:
                                    as_recorded = False
                                    break
                            gmp_trace_props = self.get_trace_properties(
                                trace, channel, loc, as_recorded
                            )
                            gmp_metrics = self.get_metrics(summary, channel, net, sta)
                            gmp_trace = Trace(
                                properties=gmp_trace_props, metrics=gmp_metrics
                            )
                            gmp_traces.append(gmp_trace)
                    if not len(gmp_traces):
                        continue
                    gmp_stream = Stream(properties=gmp_stream_props, traces=gmp_traces)
                    gmp_streams.append(gmp_stream)
                if not len(gmp_streams):
                    continue
                network_code, station_code = station_id.split(".")
                gmp_feature_props = FeatureProperties(
                    network_code=network_code,
                    station_code=station_code,
                    streams=gmp_streams,
                    name=trace.stats.standard.station_name,
                )
                lon, lat, elev = [
                    trace.stats.coordinates.longitude,
                    trace.stats.coordinates.latitude,
                    trace.stats.coordinates.elevation,
                ]
                gmp_feature_geom = FeatureGeometry(coordinates=[lon, lat, elev])
                gmp_feature = Feature(
                    geometry=gmp_feature_geom,
                    properties=gmp_feature_props,
                )
                gmp_features.append(gmp_feature)
            gmp_packet = GroundMotionPacket(
                event=gmp_event,
                provenance=gmp_provenance,
                features=gmp_features,
                version=VERSION,
            )
            outfile = pathlib.Path(
                self._gmpacket_directory, f"{eventid}_groundmotion_packet.json"
            )
            gmp_packet.save_to_json(outfile)
            files.append(outfile)
            nevents += 1

        return (files, nevents, nstreams, ntraces)

    def __del__(self):
        self._workspace.close()


class MetricHolder(object):
    float_pat = "[+-]?([0-9]*[.])?[0-9]+"  # class variable
    int_pat = r"([0-9]+)"  # class variable

    def get_dimensions(self):
        return self.dimensions

    def get_values(self):
        return self.values

    def __repr__(self) -> str:
        return f"{self.metric_type}\n{self.dimensions}\n{self.values}"


class SAMetricHolder(MetricHolder):
    def __init__(self, damping):  # damping in range 0-1
        self.dimensions = {
            "number": 2,
            "names": ["critical damping", "period"],
            "units": ["%", "s"],
            "axis_values": [[damping * 100], []],
        }
        self.values = [[]]
        self.metric_type = "SA"

    def add_value(self, value, metric_name):
        period = float(re.search(self.float_pat, metric_name).group())
        self.values[0].append(value)
        self.dimensions["axis_values"][1].append(period)


class FASMetricHolder(MetricHolder):
    def __init__(self):
        self.dimensions = {
            "number": 2,
            "names": ["period"],
            "units": ["s"],
            "axis_values": [[]],
        }
        self.values = [[]]
        self.metric_type = "FAS"

    def add_value(self, value, metric_name):
        period = float(re.search(self.float_pat, metric_name).group())
        self.values[0].append(value)
        self.dimensions["axis_values"][0].append(period)


class DurationMetricHolder(MetricHolder):
    def __init__(self):
        self.dimensions = {
            "number": 2,
            "names": ["Start percentage", "End percentage"],
            "units": ["%", "%"],
            "axis_values": [[], []],
        }
        self.values = [[]]
        self.metric_type = "DURATION"

    def add_value(self, value, metric_name):
        start_percentage, end_percentage = [
            int(v) for v in re.findall(self.int_pat, metric_name)
        ]
        self.dimensions["axis_values"][0].append(start_percentage)
        self.dimensions["axis_values"][1].append(end_percentage)
        self.values[0].append(value)
