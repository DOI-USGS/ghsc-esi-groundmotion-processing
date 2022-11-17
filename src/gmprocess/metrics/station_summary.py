# stdlib imports
import re

# third party imports
from lxml import etree
import numpy as np
import pandas as pd
from obspy.geodetics.base import gps2dist_azimuth
from openquake.hazardlib.geo import geodetic as oqgeo
from esi_utils_rupture.point_rupture import PointRupture
from esi_utils_rupture.origin import Origin
import ps2ff

# local imports
from gmprocess.utils.config import get_config
from gmprocess.metrics.gather import gather_pgms
from gmprocess.metrics.metrics_controller import MetricsController
from gmprocess.utils import constants
from gmprocess.utils.tables import _get_table_row, find_float

XML_UNITS = {
    "pga": "%g",
    "pgv": "cm/s",
    "sa": "%g",
    "arias": "m/s",
    "fas": "cm/s",
    "duration": "s",
    "sorted_duration": "s",
}

DEFAULT_DAMPING = 0.05

M_PER_KM = 1000


class StationSummary(object):
    """Class for storing/organizing station metrics.

    Note that this class is effecitvely a container for distance a waveform metric
    info for a given station. Thus, it calls the MetricsController class, which
    handles all of the actual calculations. But the distance calculations, which are
    much simpler, are done within this class.

    It also handles some difficult things like constructing itself from the XML
    that is stored in the workspace HDF5 file and provides a few different ways to
    summarize it's contents.
    """

    def __init__(self):
        """Initialize the StationSummary class."""
        self._bandwidth = None
        self._components = None
        self._coordinates = None
        self._damping = None
        self._elevation = None
        self._distances = {}
        self._back_azimuth = None
        self._imts = None
        self.event = None
        self._pgms = None
        self._smoothing = None
        self._starttime = None
        self._station_code = None
        self._stream = None
        self._summary = None
        self.rrup_interp = None
        self.rjb_interp = None
        self.channel_dict = {}

    @property
    def available_imcs(self):
        """Helper method for getting a list of components.

        Returns:
            list: List of available components (str).
        """
        return [x for x in gather_pgms()[1]]

    @property
    def available_imts(self):
        """Helper method for getting a list of measurement types.

        Returns:
            list: List of available measurement types (str).
        """
        return [x for x in gather_pgms()[0]]

    @property
    def bandwidth(self):
        """Helper method for getting the defined bandwidth.

        Returns:
            float: Bandwidth used in smoothing.
        """
        return self._bandwidth

    @property
    def components(self):
        """Helper method returning a list of requested/calculated components.

        Returns:
            list: List of requested/calculated components (str).
        """
        return list(self._components)

    @property
    def coordinates(self):
        """Helper method returning the coordinates of the station.

        Returns:
            list: List of coordinates (str).
        """
        return self._coordinates

    @property
    def damping(self):
        """Helper method for getting SA damping.

        Returns:
            float: Damping used in SA calculation.
        """
        return self._damping

    @property
    def elevation(self):
        """Helper method for getting the station elevation.

        Returns:
            float: Station elevation
        """
        return self._elevation

    @property
    def distances(self):
        """Helper method for getting the distances.

        Returns:
            dict: Dictionary of distance measurements.
        """
        return self._distances

    @classmethod
    def from_config(
        cls,
        stream,
        event,
        config=None,
        calc_waveform_metrics=True,
        calc_station_metrics=True,
        rupture=None,
        rrup_interp=None,
        rjb_interp=None,
    ):
        """
        Args:
            stream (obspy.core.stream.Stream):
                Strong motion timeseries for one station.
            event (ScalarEvent):
                Object containing latitude, longitude, depth, and magnitude.
            config (dictionary):
                Configuration dictionary.
            calc_waveform_metrics (bool):
                Whether to calculate waveform metrics. Default is True.
            calc_station_metrics (bool):
                Whether to calculate station metrics. Default is True.
            rupture (PointRupture or QuadRupture):
                esi-utils-rupture rupture object. Default is None.
            rrup_interp (dict):
                Rrup adjustment interpolation data.
            rjb_interp (dict):
                Rjb adjustment interpolation data.
        Returns:
            class: StationSummary class.

        Note:
            Assumes a processed stream with units of gal (1 cm/s^2).
            No processing is done by this class.
        """
        if config is None:
            config = get_config()
        station = cls()

        damping = config["metrics"]["sa"]["damping"]
        smoothing = config["metrics"]["fas"]["smoothing"]
        bandwidth = config["metrics"]["fas"]["bandwidth"]

        station.rrup_interp = rrup_interp
        station.rjb_interp = rjb_interp
        station._damping = damping
        station._smoothing = smoothing
        station._bandwidth = bandwidth
        station._stream = stream
        station.event = event
        station.rupture = rupture
        station.set_metadata_from_stream()

        if stream.passed and calc_waveform_metrics:
            metrics = MetricsController.from_config(stream, config=config, event=event)

            station.channel_dict = metrics.channel_dict.copy()

            pgms = metrics.pgms
            if pgms is None:
                station._components = metrics.imcs
                station._imts = metrics.imts
                station.pgms = pd.DataFrame.from_dict(
                    {"IMT": [], "IMC": [], "Result": []}
                )
            else:
                station._components = set(pgms.index.get_level_values("IMC"))
                station._imts = set(pgms.index.get_level_values("IMT"))
                station.pgms = pgms
        if calc_station_metrics:
            station.compute_station_metrics()

        return station

    @classmethod
    def from_pgms(cls, station_code, pgms):
        """
        Args:
            station_code (str):
                Station code for the given pgms.
            pgms (dict):
                Dictionary of pgms.

        Returns:
            class: StationSummary clsas.

        Note:
            The pgm dictionary must be formated as imts with subdictionaries
            containing imcs:

            ```
                {
                  'SA1.0': {
                    'H2': 84.23215974982956,
                    'H1': 135.9267934939141,
                    'GREATER_OF_TWO_HORIZONTALS': 135.9267934939141,
                    'Z': 27.436966897028416
                  },
                  ...
                }
            ```

            This should be the default format for significant ground motion
            parametric data from COMCAT.
        """
        station = cls()
        station._station_code = station_code
        dfdict = {"IMT": [], "IMC": [], "Result": []}
        for imt in pgms:
            for imc in pgms[imt]:
                dfdict["IMT"] += [imt]
                dfdict["IMC"] += [imc]
                dfdict["Result"] += [pgms[imt][imc]]
        pgmdf = pd.DataFrame.from_dict(dfdict).set_index(["IMT", "IMC"])
        station.pgms = pgmdf
        imts = [key for key in pgms]
        components = []
        for imt in pgms:
            components += [imc for imc in pgms[imt]]
        station._components = np.sort(np.unique(components))
        station._imts = np.sort(imts)
        # stream should be set later with corrected a corrected stream
        # this stream (in units of gal or 1 cm/s^2) can be used to
        # calculate and set oscillators
        return station

    @classmethod
    def from_stream(
        cls,
        stream,
        components,
        imts,
        event,
        damping=None,
        smoothing=None,
        bandwidth=None,
        allow_nans=None,
        config=None,
        calc_waveform_metrics=True,
        calc_station_metrics=True,
        rupture=None,
    ):
        """
        Args:
            stream (obspy.core.stream.Stream):
                Strong motion timeseries for one station.
            components (list):
                List of requested components (str).
            imts (list):
                List of requested imts (str).
            event (ScalarEvent):
                Origin/magnitude for the event containing time, latitude,
                longitude, depth, and magnitude.
            damping (float):
                Damping of oscillator. Default is None.
            smoothing (float):
                Smoothing method. Default is None.
            bandwidth (float):
                Bandwidth of smoothing. Default is None.
            allow_nans (bool):
                Should nans be allowed in the smoothed spectra. If False, then
                the number of points in the FFT will be computed to ensure
                that nans will not result in the smoothed spectra.
            config (dictionary):
                Configuration dictionary.
            calc_waveform_metrics (bool):
                Whether to calculate waveform metrics. Default is True.
            calc_station_metrics (bool):
                Whether to calculate station metrics. Default is True.
            rupture (PointRupture or QuadRupture):
                esi-utils-rupture rupture object. Default is None.
        Note:
            Assumes a processed stream with units of gal (1 cm/s^2).
            No processing is done by this class.
        """
        station = cls()
        station.rupture = rupture

        if config is None:
            station.config = get_config()
        else:
            station.config = config

        station._imts = np.sort(imts)
        station._components = np.sort(components)

        if damping is None:
            damping = station.config["metrics"]["sa"]["damping"]
        if smoothing is None:
            smoothing = station.config["metrics"]["fas"]["smoothing"]
        if bandwidth is None:
            bandwidth = station.config["metrics"]["fas"]["bandwidth"]
        if allow_nans is None:
            allow_nans = station.config["metrics"]["fas"]["allow_nans"]

        station._damping = damping
        station._smoothing = smoothing
        station._bandwidth = bandwidth
        station._allow_nans = allow_nans
        station._stream = stream
        station.event = event

        station.set_metadata_from_stream()

        if stream.passed and calc_waveform_metrics:
            station.compute_waveform_metrics()
        if calc_station_metrics:
            station.compute_station_metrics()
        return station

    def get_pgm(self, imt, imc):
        """Finds the imt/imc value requested.

        Args:
            imt (str):
                Requested intensity measure type.
            imc (str):
                Requested intensity measure component.

        Returns:
            float: Value for the imt, imc requested.
        """
        imt = imt.upper()
        imc = imc.upper()
        if imt not in self.imts or imc not in self.components:
            return np.nan
        else:
            return self.pgms.Result.loc[imt, imc]

    def get_summary(self):
        columns = ["STATION", "NAME", "SOURCE", "NETID", "LAT", "LON", "ELEVATION"]
        if self._distances is not None:
            for dist_type in self._distances:
                columns.append(dist_type.upper() + "_DISTANCE")
        # set meta_data
        row = np.zeros(len(columns), dtype=list)
        row[0] = self.station_code
        name_str = self.stream[0].stats["standard"]["station_name"]
        row[1] = name_str
        source = self.stream[0].stats.standard["source"]
        row[2] = source
        row[3] = self.stream[0].stats["network"]
        row[4] = self.coordinates[0]
        row[5] = self.coordinates[1]
        row[6] = self.elevation
        imcs = self.components
        imts = self.imts
        pgms = self.pgms
        meta_columns = pd.MultiIndex.from_product([columns, [""]])
        meta_dataframe = pd.DataFrame(np.array([row]), columns=meta_columns)
        pgm_columns = pd.MultiIndex.from_product([imcs, imts])
        pgm_data = np.zeros((1, len(imts) * len(imcs)))
        subindex = 0
        for imc in imcs:
            for imt in imts:
                try:
                    value = pgms.Result.loc[imt, imc]
                except KeyError:
                    value = np.nan
                pgm_data[0][subindex] = value
                subindex += 1
        pgm_dataframe = pd.DataFrame(pgm_data, columns=pgm_columns)
        dataframe = pd.concat([meta_dataframe, pgm_dataframe], axis=1)
        return dataframe

    @property
    def imts(self):
        """Helper method returning a list of requested/calculated measurement types.

        Returns:
            list: List of requested/calculated measurement types (str).
        """
        return list(self._imts)

    @property
    def pgms(self):
        """Helper method returning a station's pgms.

        Returns:
            dictionary: Pgms for each imt and imc.
        """
        return self._pgms

    @pgms.setter
    def pgms(self, pgms):
        """Helper method to set the pgms attribute.

        Args:
            pgms (list): Dictionary of pgms for each imt and imc.
        """
        self._pgms = pgms

    def set_metadata_from_stream(self):
        """Set the metadata for the station."""
        stats = self.stream[0].stats
        self._starttime = stats.starttime
        self._station_code = stats.station
        if "coordinates" not in stats:
            self._elevation = np.nan
            self._coordinates = (np.nan, np.nan)
            return
        lat = stats.coordinates.latitude
        lon = stats.coordinates.longitude
        if "elevation" not in stats.coordinates or np.isnan(
            stats.coordinates.elevation
        ):
            elev = 0
        else:
            elev = stats.coordinates.elevation
        self._elevation = elev
        self._coordinates = (lat, lon)

    @property
    def smoothing(self):
        """
        Helper method for getting the defined smoothing used for the
        calculation FAS.

        Returns:
            string: Smoothing method used.
        """
        return self._smoothing

    @property
    def starttime(self):
        """
        Helper method returning a station's starttime.

        Returns:
            str: Start time for one station.
        """
        return self._starttime

    @property
    def station_code(self):
        """
        Helper method returning a station's station code.

        Returns:
            str: Station code for one station.
        """
        return self._station_code

    @property
    def stream(self):
        """
        Helper method returning a station's stream.

        Returns:
            obspy.core.stream.Stream: Stream for one station.
        """
        return self._stream

    @property
    def summary(self):
        """
        Helper method returning a station's summary.

        Returns:
            pandas.Dataframe: Summary for one station.
        """
        return self.get_summary()

    @classmethod
    def from_xml(cls, xml_stream, xml_station):
        """Instantiate a StationSummary from metrics XML stored in ASDF file.

        <waveform_metrics>
            <rot_d50>
                <pga units="m/s**2">0.45</pga>
                <sa percent_damping="5.0" units="g">
                <value period="2.0">0.2</value>
            </rot_d50>
            <maximum_component>
            </maximum_component>
        </waveform_metrics>

        <station_metrics>
            <distances>
            <hypocentral units="km">100</hypocentral>
            <epicentral units="km">120</epicentral>
            </distances>
        </station_metrics>

        Args:
            xml_stream (str):
                Stream metrics XML string in format above.
            xml_station (str):
                Station metrics XML string in format above.

        Returns:
            object: StationSummary Object summarizing all station metrics.

        """
        imtlist = gather_pgms()[0]
        root = etree.fromstring(xml_stream)
        pgms = {}
        channel_dict = {}
        damping = None
        for element in root.iter():
            etag = element.tag
            if etag == "waveform_metrics":
                station_code = element.attrib["station_code"]
                continue
            elif etag in imtlist:
                tdict = {}
                if etag in ["sa", "fas"]:
                    period = element.attrib["period"]
                    if "damping" in element.attrib:
                        damping = float(element.attrib["damping"])
                    imt = f"{etag.upper()}({period})"
                elif etag == "duration":
                    interval = element.attrib["interval"]
                    imt = f"{etag.upper()}{interval}"
                else:
                    imt = etag.upper()
                for imc_element in element.getchildren():
                    imc = imc_element.tag.upper()
                    if imc in ["H1", "H2", "Z"]:
                        if "original_channel" in imc_element.attrib:
                            channel_dict[imc] = imc_element.attrib["original_channel"]
                    value = float(imc_element.text)
                    tdict[imc] = value

                pgms[imt] = tdict

        station = cls.from_pgms(station_code, pgms)

        station._damping = damping
        station.channel_dict = channel_dict.copy()
        # extract info from station metrics, fill in metadata
        root = etree.fromstring(xml_station)  # station metrics element
        station._distances = {}
        for element in root.iterchildren():
            if element.tag == "distances":
                for dist_type in element.iterchildren():
                    station._distances[dist_type.tag] = float(dist_type.text)
            if element.tag == "back_azimuth":
                station._back_azimuth = float(element.text)

        return station

    def compute_station_metrics(self):
        """Calculate station metrics"""
        lat, lon = self.coordinates
        elev = self.elevation

        if self.rrup_interp is None or self.rjb_interp is None:
            self.rrup_interp, self.rjb_interp = get_ps2ff_interpolation(self.event)

        if self.event is not None:
            event = self.event
            geo_tuple = gps2dist_azimuth(lat, lon, event.latitude, event.longitude)
            sta_repi = geo_tuple[0] / M_PER_KM
            sta_baz = geo_tuple[1]
            sta_rhyp = oqgeo.distance(
                lon,
                lat,
                -elev / M_PER_KM,
                event.longitude,
                event.longitude,
                event.depth,
            )

        if self.rupture is None:
            origin = Origin(
                {
                    "id": "",
                    "netid": "",
                    "network": "",
                    "lat": event.latitude,
                    "lon": event.longitude,
                    "depth": event.depth,
                    "locstring": "",
                    "mag": event.magnitude,
                    "time": "",
                    "mech": "",
                    "productcode": "",
                }
            )
            self.rupture = PointRupture(origin)

        if isinstance(self.rupture, PointRupture):
            rjb_mean = np.interp(
                sta_repi,
                self.rjb_interp["repi"],
                self.rjb_interp["rjb_hat"],
            )
            rjb_var = np.interp(
                sta_repi,
                self.rjb_interp["repi"],
                self.rjb_interp["rjb_var"],
            )
            rrup_mean = np.interp(
                sta_repi,
                self.rrup_interp["repi"],
                self.rrup_interp["rrup_hat"],
            )
            rrup_var = np.interp(
                sta_repi,
                self.rrup_interp["repi"],
                self.rrup_interp["rrup_var"],
            )
            gc2_rx = np.full_like(rjb_mean, np.nan)
            gc2_ry = np.full_like(rjb_mean, np.nan)
            gc2_ry0 = np.full_like(rjb_mean, np.nan)
            gc2_U = np.full_like(rjb_mean, np.nan)
            gc2_T = np.full_like(rjb_mean, np.nan)
        else:
            rrup_mean, rrup_var = self.rupture.computeRrup(
                np.array([lon]),
                np.array([lat]),
                constants.ELEVATION_FOR_DISTANCE_CALCS,
            )
            rjb_mean, rjb_var = self.rupture.computeRjb(
                np.array([lon]),
                np.array([lat]),
                constants.ELEVATION_FOR_DISTANCE_CALCS,
            )
            rrup_var = np.full_like(rrup_mean, np.nan)
            rjb_var = np.full_like(rjb_mean, np.nan)
            gc2_dict = self.rupture.computeGC2(
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
            bazs = []
            for quad in self.rupture._quadrilaterals:
                P0, P1, _, _ = quad
                for point in [P0, P1]:
                    dist, _, baz = gps2dist_azimuth(
                        point.y,
                        point.x,
                        lat,
                        lon,
                    )
                    dists.append(dist)
                    bazs.append(baz)
                sta_baz = bazs[np.argmin(dists)]

        self._distances = {
            "epicentral": sta_repi,
            "hypocentral": sta_rhyp,
            "rupture": rrup_mean,
            "rupture_var": rrup_var,
            "joyner_boore": rjb_mean,
            "joyner_boore_var": rjb_var,
            "gc2_rx": gc2_rx,
            "gc2_ry": gc2_ry,
            "gc2_ry0": gc2_ry0,
            "gc2_U": gc2_U,
            "gc2_T": gc2_T,
        }
        self._back_azimuth = sta_baz

    def compute_waveform_metrics(self):
        """Calculate waveform metrics"""
        if self.stream.passed:
            metrics = MetricsController(
                self.imts,
                self.components,
                self.stream,
                bandwidth=self.bandwidth,
                allow_nans=self._allow_nans,
                damping=self.damping,
                event=self.event,
                smooth_type=self.smoothing,
            )

            self.channel_dict = metrics.channel_dict.copy()
            self.pgms = metrics.pgms
            if not len(self.pgms):
                self._components = metrics.imcs
                self._imts = metrics.imts
                self.pgms = pd.DataFrame.from_dict({"IMT": [], "IMC": [], "Result": []})
            else:
                self._components = set(self.pgms.index.get_level_values("IMC"))
                self._imts = set(self.pgms.index.get_level_values("IMT"))
                self.pgms = self.pgms

    def get_metric_xml(self):
        """Return waveform metrics XML as defined for our ASDF implementation.

        Returns:
            str: XML in the form:
                <waveform_metrics>
                    <rot_d50>
                        <pga units="m/s**2">0.45</pga>
                        <sa percent_damping="5.0" units="g">
                        <value period="2.0">0.2</value>
                    </rot_d50>
                    <maximum_component>
                    </maximum_component>
                </waveform_metrics>

        Raises:
            KeyError: if the requrested imt is not present.
        """
        FLOAT_MATCH = r"[0-9]*\.[0-9]*"
        root = etree.Element("waveform_metrics", station_code=self.station_code)
        for imt in self.imts:
            imtstr = imt.lower()
            units = None
            if imtstr in XML_UNITS:
                units = XML_UNITS[imtstr]
            else:
                for key in XML_UNITS.keys():
                    if imtstr.startswith(key):
                        units = XML_UNITS[key]
                        break
            if units is None:
                raise KeyError(f"Could not find units for IMT {imtstr}")

            period = None
            if imtstr.startswith("sa") or imtstr.startswith("fas"):
                period = float(re.search(FLOAT_MATCH, imtstr).group())
                attdict = {
                    "period": (
                        constants.METRICS_XML_FLOAT_STRING_FORMAT["period"] % period
                    ),
                    "units": units,
                }
                if imtstr.startswith("sa"):
                    imtstr = "sa"
                    damping = self._damping
                    if damping is None:
                        damping = DEFAULT_DAMPING
                    attdict["damping"] = (
                        constants.METRICS_XML_FLOAT_STRING_FORMAT["damping"] % damping
                    )
                else:
                    imtstr = "fas"
                imt_tag = etree.SubElement(root, imtstr, attrib=attdict)
            elif imtstr.startswith("duration"):
                attdict = {"interval": imtstr.replace("duration", ""), "units": units}
                imtstr = "duration"
                imt_tag = etree.SubElement(root, imtstr, attrib=attdict)
            else:
                imt_tag = etree.SubElement(root, imtstr, units=units)

            for imc in self.components:
                imcstr = imc.lower().replace("(", "").replace(")", "")
                if imc in ["H1", "H2", "Z"]:
                    attributes = {"original_channel": self.channel_dict[imc]}
                else:
                    attributes = {}
                imc_tag = etree.SubElement(imt_tag, imcstr, attrib=attributes)
                try:
                    value = self.pgms.Result.loc[imt, imc]
                except KeyError:
                    value = np.nan
                imc_tag.text = constants.METRICS_XML_FLOAT_STRING_FORMAT["pgm"] % value
        xmlstr = etree.tostring(root, pretty_print=True, encoding="unicode")
        return xmlstr

    def get_station_xml(self):
        """Return XML for station metrics as defined for our ASDF implementation.

        Returns:
            str: XML in the form specified by format.
        """

        root = etree.Element("station_metrics", station_code=self.station_code)

        if self._back_azimuth is not None:
            back_azimuth = etree.SubElement(root, "back_azimuth")
            back_azimuth.text = (
                constants.METRICS_XML_FLOAT_STRING_FORMAT["back_azimuth"]
                % self._back_azimuth
            )

        if self._distances:
            distances = etree.SubElement(root, "distances")
            for dist_type in self._distances:
                element = etree.SubElement(distances, dist_type, units="km")
                element.text = (
                    constants.METRICS_XML_FLOAT_STRING_FORMAT["distance"]
                    % self._distances[dist_type]
                )

        return etree.tostring(root, pretty_print=True, encoding="unicode")

    def get_imc_dict(self, imc=None):
        """Get an IMC table.

        Args:
            imc (str or list):
                String of list of strings specifying the requested IMC.

        Returns:
            A dictionary with keys corresponding to IMCs, where the associated
            value is a dictionary with keys corresponding to IMTs.
        """
        imc_dict = {}
        pgms = self.pgms
        if imc is None:
            imclist = pgms.index.get_level_values("IMC").unique().tolist()
        elif not isinstance(imc, list):
            imclist = [imc]
        else:
            imclist = imc

        # Note: in this situation, we can only have 1 row per "table" where the
        # different IMTs are the different columns.
        for imc in imclist:
            row = _get_table_row(self._stream, self, self.event, imc)
            if not len(row):
                continue
            imc_dict[imc] = row
        return imc_dict

    def get_sa_arrays(self, imc=None):
        """Get an SA arrays for selected IMCs.

        Args:
            imc (str or list):
                String of list of strings specifying the requested IMC.

        Returns:
            A dictionary with keys corresponding to IMCs, where the associated
            value is a dictionary with keys of 'period' and 'sa' which are
            numpy arrays.
        """
        imc_dict = self.get_imc_dict(imc)
        sa_arrays = {}
        for imc_key, id in imc_dict.items():
            period = []
            sa = []
            for imt, val in id.items():
                tmp_period = find_float(imt)
                if tmp_period is not None:
                    period.append(tmp_period)
                    sa.append(val)
            period = np.array(period)
            sa = np.array(sa)
            idx = np.argsort(period)
            sa_arrays[imc_key] = {"period": period[idx], "sa": sa[idx]}
        return sa_arrays


def get_ps2ff_interpolation(event):
    """Construct interpolation data for approximating Rrup and Rjb.

    Args:
        event (gmprocess.utils.event.ScalarEvent):
            A ScalarEvent object.

    Returns:
        tuple: Rrup spline, Rjb spline
    """
    # TODO: Make these options configurable in config file.
    mscale = ps2ff.constants.MagScaling.WC94
    smech = ps2ff.constants.Mechanism.A
    aspect = 1.7
    mindip_deg = 10.0
    maxdip_deg = 90.0
    mindip = mindip_deg * np.pi / 180.0
    maxdip = maxdip_deg * np.pi / 180.0
    repi, Rjb_hat, Rrup_hat, Rjb_var, Rrup_var = ps2ff.run.single_event_adjustment(
        event.magnitude,
        event.depth,
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
        "rjb_hat": Rjb_hat,
        "rjb_var": Rjb_var,
    }
    rrup_interp = {
        "repi": repi,
        "rrup_hat": Rrup_hat,
        "rrup_var": Rrup_var,
    }
    return rrup_interp, rjb_interp
