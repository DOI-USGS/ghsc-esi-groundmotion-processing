"""Module for storing and organizing station metrics"""

import logging

import numpy as np
import ps2ff.run
import ps2ff.constants
from obspy.geodetics.base import gps2dist_azimuth
from openquake.hazardlib.geo import geodetic as oqgeo

from esi_utils_rupture.point_rupture import PointRupture
from esi_utils_rupture.origin import Origin
from esi_utils_rupture.factory import get_rupture

from gmprocess.utils import constants
from gmprocess.metrics.metric_collection_base import MetricCollection
from gmprocess.metrics.station_metric import StationMetric
from gmprocess.io.asdf.station_metrics_xml import StationMetricsXML
from gmprocess.io.asdf.path_utils import get_stream_path
from gmprocess.io.asdf.stream_workspace import array_to_str


class StationMetricCollection(MetricCollection):
    """StationMetricCollection class.

    This class is intended to hold a collection of StationMetric objects, which are
    stored as a list in the "station_metrics" attribute.
    """

    def __init__(self):
        """Constructor for StationMetricCollection object."""
        self.station_metrics = []
        self.stream_paths = []

    def __repr__(self):
        n_metrics = len(self.station_metrics)
        return f"StationMetricCollection: {n_metrics} metrics"

    def extend(self, metric):
        """extend to a StationMetricCollection.

        Args:
            metric (StationMetricCollection)
                Metric collection to append.
        """
        if not isinstance(metric, StationMetricCollection):
            raise ValueError("Extending metric must be a StationMetricCollection.")
        self.station_metrics.extend(metric.station_metrics)

    @classmethod
    def from_streams(cls, streams, event, config, rupture_file=None):
        """Construct the StationMetricCollection from a list of StationStreams.

        Args:
            streams (list):
                List of StationStream objects.
            event (gmprocess.utils.scalar_event.ScalarEvent):
                A ScalarEvent object.
            config (dict):
                Dictionary of config options.
            rupture_file (str):
                Path to rupture file.
        """

        smc = cls()
        smc.calculate_metrics(streams, event, config, rupture_file)
        return smc

    @classmethod
    def from_workspace(cls, workspace):
        """Construct the StationMetricCollection from a StreamWorkspace file.

        Args:
            workspace (StreamWorkspace):
                StreamWorkspace object.
        """
        smc = cls()
        smc.get_metrics_from_workspace(workspace)
        return smc

    def get_metrics_from_workspace(self, workspace):
        """Populate station metrics from a workspace file.

        Args:
            workspace (StreamWorkspace):
                StreamWorkspace object.
        """

        if "StationMetrics" not in workspace.dataset.auxiliary_data:
            logging.info("StationMetrics not in auxiliary data.")
            return

        for metric in workspace.dataset.auxiliary_data.StationMetrics:
            metric_list = metric.list()
            for stream_path in metric_list:
                metric_data = array_to_str(metric[stream_path].data)
                self.station_metrics.append(
                    StationMetricsXML.from_xml(metric_data).metrics
                )
                self.stream_paths.append(stream_path)

    def calculate_metrics(
        self, streams, event, config, rupture_file=None, label="default"
    ):
        """Calculate station metrics from a list of streams.

        Args:
            streams (list):
                List of StationStream objects.
            event (gmprocess.utils.scalar_event.ScalarEvent):
                A ScalarEvent object.
            config (dict):
                Dictionary of config options.
            rupture_file (str):
                Path to rupture file.
            label (str):
                Processing label.
        """
        origin = Origin(
            {
                "id": event.id.replace("smi:local/", ""),
                "netid": "",
                "network": "",
                "lat": event.latitude,
                "lon": event.longitude,
                "depth": event.depth_km,
                "locstring": "",
                "mag": event.magnitude,
                "time": event.time,
                "mech": "",
                "reference": "",
                "productcode": "",
            }
        )
        rupture = get_rupture(origin, rupture_file)

        # Note: tag for station metrics does not have processing label
        tag = origin.id

        rrup_interp, rjb_interp = self.get_ps2ff_interpolation(origin)

        for stream in streams:
            coord_dict = stream[0].stats.coordinates
            lat = coord_dict["latitude"]
            lon = coord_dict["longitude"]
            elev = coord_dict["elevation"]

            geo_tuple = gps2dist_azimuth(lat, lon, origin.lat, origin.lon)
            sta_repi = geo_tuple[0] / constants.M_PER_KM
            sta_baz = geo_tuple[1]
            sta_rhyp = oqgeo.distance(
                lon,
                lat,
                -elev / constants.M_PER_KM,
                origin.lon,
                origin.lat,
                origin.depth,
            )

            if isinstance(rupture, PointRupture):
                rjb_mean = np.interp(
                    sta_repi,
                    rjb_interp["repi"],
                    rjb_interp["rjb_hat"],
                )
                rjb_var = np.interp(
                    sta_repi,
                    rjb_interp["repi"],
                    rjb_interp["rjb_var"],
                )
                rrup_mean = np.interp(
                    sta_repi,
                    rrup_interp["repi"],
                    rrup_interp["rrup_hat"],
                )
                rrup_var = np.interp(
                    sta_repi,
                    rrup_interp["repi"],
                    rrup_interp["rrup_var"],
                )
                gc2_rx = np.full_like(rjb_mean, np.nan)
                gc2_ry = np.full_like(rjb_mean, np.nan)
                gc2_ry0 = np.full_like(rjb_mean, np.nan)
                gc2_U = np.full_like(rjb_mean, np.nan)
                gc2_T = np.full_like(rjb_mean, np.nan)
            else:
                rrup_mean, rrup_var = rupture.computeRrup(
                    np.array([lon]),
                    np.array([lat]),
                    constants.ELEVATION_FOR_DISTANCE_CALCS,
                )
                rjb_mean, rjb_var = rupture.computeRjb(
                    np.array([lon]),
                    np.array([lat]),
                    constants.ELEVATION_FOR_DISTANCE_CALCS,
                )
                rrup_var = np.full_like(rrup_mean, np.nan)
                rjb_var = np.full_like(rjb_mean, np.nan)
                gc2_dict = rupture.computeGC2(
                    np.array([lon]),
                    np.array([lat]),
                    constants.ELEVATION_FOR_DISTANCE_CALCS,
                )
                gc2_rx = gc2_dict["rx"]
                gc2_ry = gc2_dict["ry"]
                gc2_ry0 = gc2_dict["ry0"]
                gc2_U = gc2_dict["U"]
                gc2_T = gc2_dict["T"]

                # If we don't have a point rupture, then back azimuth needs
                # to be calculated to the closest point on the rupture
                dists = []
                back_azis = []
                for quad in rupture.getQuadrilaterals():
                    P0, P1, _, _ = quad
                    for point in [P0, P1]:
                        dist, _, back_azi = gps2dist_azimuth(
                            point.y,
                            point.x,
                            lat,
                            lon,
                        )
                        dists.append(dist)
                        back_azis.append(back_azi)
                    sta_baz = back_azis[np.argmin(dists)]

            sm = StationMetric(
                repi=sta_repi,
                rhyp=sta_rhyp,
                rrup_mean=rrup_mean,
                rrup_var=rrup_var,
                rjb_mean=rjb_mean,
                rjb_var=rjb_var,
                gc2_rx=gc2_rx,
                gc2_ry=gc2_ry,
                gc2_ry0=gc2_ry0,
                gc2_U=gc2_U,
                gc2_T=gc2_T,
                back_azimuth=sta_baz,
            )
            self.station_metrics.append(sm)
            self.stream_paths.append(get_stream_path(stream, tag, config))

    @staticmethod
    def get_ps2ff_interpolation(origin):
        """Construct interpolation data for approximating Rrup and Rjb.

        Args:
            origin (Origin):
                An Origin object.

        Returns:
            tuple: Rrup spline, Rjb spline
        """
        # TODO: Make these options configurable in config file.
        mscale = ps2ff.constants.MagScaling.WC94
        smech = ps2ff.constants.Mechanism.A
        aspect = 1.7
        mindip_deg = 40.0
        maxdip_deg = 90.0
        mindip = mindip_deg * np.pi / 180.0
        maxdip = maxdip_deg * np.pi / 180.0
        repi, rjb_hat, rrup_hat, rjb_var, rrup_var = ps2ff.run.single_event_adjustment(
            origin.mag,
            origin.depth,
            ar=aspect,
            mechanism=smech,
            mag_scaling=mscale,
            n_repi=30,
            min_repi=0.01,
            max_repi=2000,
            nxny=7,
            n_theta=19,
            n_dip=4,
            min_dip=mindip,
            max_dip=maxdip,
            n_eps=5,
            trunc=2,
        )
        rjb_interp = {
            "repi": repi,
            "rjb_hat": rjb_hat,
            "rjb_var": rjb_var,
        }
        rrup_interp = {
            "repi": repi,
            "rrup_hat": rrup_hat,
            "rrup_var": rrup_var,
        }
        return rrup_interp, rjb_interp
