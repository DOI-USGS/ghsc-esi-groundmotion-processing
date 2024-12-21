# stdlib imports
import logging
import tempfile

# third party imports
import pytz
from gmprocess.core.streamcollection import StreamCollection

# local imports
from gmprocess.io.fetcher import DataFetcher
from gmprocess.io.obspy.core import read_obspy
from gmprocess.utils.config import get_config

from obspy.clients.fdsn import Client
from obspy.clients.fdsn.header import URL_MAPPINGS, FDSNException
from obspy.clients.fdsn.mass_downloader import (
    CircularDomain,
    MassDownloader,
    RectangularDomain,
    Restrictions,
)
from obspy.core.utcdatetime import UTCDateTime

OBSPY_LOGGER = "obspy.clients.fdsn.mass_downloader"

GEONET_ARCHIVE_DAYS = 7 * 86400
GEONET_ARCHIVE_URL = "http://service.geonet.org.nz"
GEO_NET_ARCHIVE_KEY = "GEONET"
GEONET_REALTIME_URL = "http://service-nrt.geonet.org.nz"

BAD_PROVIDERS = ["IRISPH5", "UIB-NORSAR"]

DEFAULT_NTHREADS = 3


class FDSNFetcher(DataFetcher):
    BOUNDS = [-180, 180, -90, 90]

    def __init__(
        self,
        time,
        lat,
        lon,
        depth,
        magnitude,
        config=None,
        rawdir=None,
        drop_non_free=True,
        stream_collection=True,
    ):
        """Create an FDSNFetcher instance.

        Download waveform data from the all available FDSN sites
        using the Obspy mass downloader functionality.

        Args:
            time (datetime):
                Origin time.
            lat (float):
                Origin latitude.
            lon (float):
                Origin longitude.
            depth (float):
                Origin depth.
            magnitude (float):
                Origin magnitude.
            config (dict):
                Dictionary containing configuration.
                If None, retrieve global config.
            rawdir (str):
                Path to location where raw data will be stored.
                If not specified, raw data will be deleted.
            drop_non_free (bool):
                Option to ignore non-free-field (borehole, sensors on
                structures, etc.)
            stream_collection (bool):
                Construct and return a StreamCollection instance?
        """
        if config is None:
            config = get_config()

        tz = pytz.UTC
        if isinstance(time, UTCDateTime):
            time = time.datetime
        self.time = tz.localize(time)
        self.lat = lat
        self.lon = lon
        self.depth = depth
        self.magnitude = magnitude
        self.config = config
        self.rawdir = rawdir
        self.drop_non_free = drop_non_free
        self.stream_collection = stream_collection

    def get_matching_events(self, solve=True):
        """Return a list of dictionaries matching input parameters.

        Args:
            solve (bool):
                If set to True, then this method
                should return a list with a maximum of one event.

        Returns:
            list: List of event dictionaries, with fields:
                  - time Event time (UTC)
                  - lat Event latitude
                  - lon Event longitude
                  - depth Event depth
                  - mag Event magnitude
        """
        pass

    def retrieve_data(self):
        """Retrieve data from many FDSN services, turn into StreamCollection.

        Args:
            event (dict):
                Best dictionary matching input event, fields as above
                in return of get_matching_events().

        Returns:
            StreamCollection: StreamCollection object.
        """
        # Bail out if FDSNFetcher not configured
        if "FDSNFetcher" not in self.config["fetchers"]:
            return

        fdsn_conf = self.config["fetchers"]["FDSNFetcher"]
        rawdir = self.rawdir

        if self.rawdir is None:
            rawdir = tempfile.mkdtemp()
        else:
            rawdir.mkdir(exist_ok=True)

        # use the mass downloader to retrieve data of interest from any FSDN
        # service.
        origin_time = UTCDateTime(self.time)

        # The Obspy mass downloader has it's own logger - grab that stream
        # and write it to our own log file
        ldict = logging.Logger.manager.loggerDict
        if OBSPY_LOGGER in ldict:
            root = logging.getLogger()
            fhandler = root.handlers[0]
            obspy_logger = logging.getLogger(OBSPY_LOGGER)
            try:
                obspy_stream_handler = obspy_logger.handlers[0]
                obspy_logger.removeHandler(obspy_stream_handler)
            except IndexError:
                pass

            obspy_logger.addHandler(fhandler)

        # Circular domain around the epicenter.
        if fdsn_conf["domain"]["type"] == "circular":
            dconf = fdsn_conf["domain"]["circular"]
            if dconf["use_epicenter"]:
                dconf["latitude"] = self.lat
                dconf["longitude"] = self.lon
            dconf.pop("use_epicenter")
            domain = CircularDomain(**dconf)
        elif fdsn_conf["domain"]["type"] == "rectangular":
            dconf = fdsn_conf["domain"]["rectangular"]
            domain = RectangularDomain(**dconf)
        else:
            raise ValueError('Domain type must be either "circular" or "rectangular".')

        rconf = fdsn_conf["restrictions"]

        rconf["starttime"] = origin_time - rconf["time_before"]
        rconf["endtime"] = origin_time + rconf["time_after"]
        rconf.pop("time_before")
        rconf.pop("time_after")

        restrictions = Restrictions(**rconf)

        providers = URL_MAPPINGS
        for bad in BAD_PROVIDERS:
            if bad in providers.keys():
                del providers[bad]

        debug = logging.getLevelName(root.level) == "DEBUG"

        selected_providers = []
        providers_conf = fdsn_conf["providers"]
        if providers_conf is not None:
            for providers_dict in providers_conf:
                key_list = list(providers_dict.keys())

                if len(key_list) != 1:
                    raise ValueError("Each provider must contain exactly one key.")

                provider_name = key_list[0]
                selected_provider_dict = {}
                selected_provider_dict["name"] = provider_name
                nthreads = DEFAULT_NTHREADS
                if "threads" in providers_dict[provider_name]:
                    nthreads = providers_dict[provider_name]["threads"]
                selected_provider_dict["threads"] = nthreads
                if providers_dict[provider_name] is None:
                    # User has not provided a conf dict for this provider, thus the
                    # provider must be in obspy's list of providers
                    if provider_name in providers:
                        selected_provider_dict["url"] = providers[provider_name]
                    else:
                        raise ValueError(
                            f"No info provided for fdsn provider {provider_name} and "
                            "this provider is not found in URL_MAPPINGS."
                        )
                else:
                    # User has provided a conf dict for this provider
                    if "url" in providers_dict[provider_name]:
                        # Use url provided by conf
                        selected_provider_dict["url"] = providers_dict[provider_name][
                            "url"
                        ]
                    elif provider_name in providers:
                        selected_provider_dict["url"] = providers[provider_name]
                    else:
                        raise ValueError(
                            f"No url provided for fdsn provider {provider_name} and "
                            "this provider is not found in URL_MAPPINGS."
                        )
                    if "bounds" in providers_dict[provider_name]:
                        selected_provider_dict["bounds"] = providers_dict[
                            provider_name
                        ]["bounds"]
                selected_providers.append(selected_provider_dict)
        else:
            selected_providers = [{"name": p} for p in providers]

        # For each of the providers, check if we have a username and password provided
        # in the config. If we do, initialize the client with the username and password.
        # Otherwise, use default initalization.

        client_groups = {}
        for provider_dict in selected_providers:
            if provider_dict["name"] == GEO_NET_ARCHIVE_KEY:
                dt = UTCDateTime.utcnow() - UTCDateTime(self.time)
                if dt < GEONET_ARCHIVE_DAYS:
                    provider_dict["url"] = GEONET_REALTIME_URL
            if "bounds" in provider_dict:
                bounds = provider_dict["bounds"]
                if bounds[0] > bounds[1]:  # crossing meridian
                    lontest = self.lon
                    cmpxmax = bounds[1] + 360
                    if self.lon < 0:
                        lontest = self.lon + 360
                    outside_lon = lontest > cmpxmax or lontest < bounds[0]
                else:
                    outside_lon = self.lon > bounds[1] or self.lon < bounds[0]
                outside_lat = self.lat > bounds[3] or self.lat < bounds[2]
                outside_lon = self.lon > bounds[1] or self.lon < bounds[0]
                if outside_lat or outside_lon:
                    continue
            try:
                # Is authentication information configured?
                fdsn_auth = self.config["fetchers"]["FDSNFetcher"]["authentication"]
                fdsn_user = fdsn_auth[provider_dict["name"]]["user"]
                fdsn_password = fdsn_auth[provider_dict["name"]]["password"]
            except KeyError:
                fdsn_user = None
                fdsn_password = None

            try:
                provider_key = ""
                if "url" in provider_dict:
                    # The provider(s) is/are supplied as a URL via the config file
                    provider_key = "url"

                else:
                    # The provider(s) is/are supplied as a "base" name, ex: "IRIS"
                    provider_key = "name"

                client = Client(
                    base_url=provider_dict[provider_key],
                    user=fdsn_user,
                    password=fdsn_password,
                    debug=debug,
                )
                nthreads = provider_dict["threads"]
                if nthreads in client_groups:
                    client_groups[nthreads].append(client)
                else:
                    client_groups[nthreads] = [client]
            except FDSNException:
                # If the FDSN service is down, then an FDSNException is raised
                logging.warning(f"Unable to initalize client {provider_dict['name']}")

        if len(client_groups):

            # break the client list into groups by number of threads specified
            # each FDSN provider can have the number of threads configured
            # default is three if not specified

            for nthreads, client_list in client_groups.items():

                # Pass off the initalized clients to the Mass Downloader
                if debug:
                    mdl = MassDownloader(providers=client_list, debug=True)
                else:
                    try:
                        # Need to turn off built in logging for ObsPy>=1.3.0
                        mdl = MassDownloader(
                            providers=client_list, configure_logging=False
                        )
                    except TypeError:
                        # For ObsPy<1.3.0 the configure_logging parameter doesn't exist
                        mdl = MassDownloader(providers=client_list)

                logging.info(f"Downloading new MiniSEED files... (using {nthreads})")
                # The data will be downloaded to the ``./waveforms/`` and
                # ``./stations/`` folders with automatically chosen file names.
                mdl.download(
                    domain,
                    restrictions,
                    mseed_storage=str(rawdir),
                    stationxml_storage=str(rawdir),
                    threads_per_client=nthreads,
                )

            if self.stream_collection:
                seed_files = rawdir.glob("*.mseed")
                streams = []
                for seed_file in seed_files:
                    try:
                        tstreams = read_obspy(seed_file, self.config)
                    except BaseException as e:
                        tstreams = None
                        fmt = 'Could not read seed file %s - "%s"'
                        logging.info(fmt % (seed_file, str(e)))
                    if tstreams is None:
                        continue
                    else:
                        streams += tstreams

                stream_collection = StreamCollection(
                    streams=streams, drop_non_free=self.drop_non_free
                )
                return stream_collection
            else:
                return None
