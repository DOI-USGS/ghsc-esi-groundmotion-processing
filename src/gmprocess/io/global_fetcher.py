# stdlib imports
import importlib
import inspect
import logging
import pathlib

import numpy as np

from obspy.geodetics import kilometers2degrees

# local imports
from .fetcher import DataFetcher
from gmprocess.utils.config import get_config
from gmprocess.io.utils import _walk
from gmprocess.io.dynamic_search_parameters import SearchParameters

FETCHER_DIRS = [
    "cosmos",
    "knet",
    "obspy",
]


def fetch_data(
    time,
    lat,
    lon,
    depth,
    magnitude,
    config=None,
    rawdir=None,
    drop_non_free=True,
    stream_collection=True,
    strec=None,
):
    """Retrieve data using any DataFetcher subclass.

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
            Project config dictionary.
        rawdir (str):
            Path to location where raw data will be stored. If not specified, raw data
            will be deleted.
        drop_non_free (bool):
            Option to ignore non-free-field (borehole, sensors on structures, etc.)
        stream_collection (bool):
            Construct and return a StreamCollection instance?
        strec (STREC):
            STREC object.

     Returns:
        StreamCollection: StreamCollection object.
    """
    if config is None:
        config = get_config()

    # Update the search parameters for the fetchers if it is enabled
    if config["fetchers"]["search_parameters"]["enabled"]:
        search_pars = SearchParameters(magnitude, config, strec)
        update_distance = np.round(search_pars.distance)
        logging.info(f"Updating search radius to {update_distance} km")
        config["fetchers"]["KNETFetcher"]["radius"] = update_distance
        config["fetchers"]["CESMDFetcher"]["eq_radius"] = update_distance
        fdsn_conf = config["fetchers"]["FDSNFetcher"]
        fdsn_conf["domain"]["circular"]["maxradius"] = kilometers2degrees(
            update_distance
        )
        # convert min to sec
        update_duration = np.round(search_pars.duration * 60)
        logging.info(f"Updating time_after to {update_duration} sec")
        fdsn_conf["restrictions"]["time_after"] = update_duration

    tfetchers = find_fetchers(lat, lon)

    # Remove fetchers if they are not present in the conf file
    fetchers = {
        k: v
        for k, v in tfetchers.items()
        if k in config["fetchers"]
        if config["fetchers"][k]["enabled"]
    }
    for fname in fetchers.keys():
        if fname not in config["fetchers"]:
            del fetchers[fname]

    instances = []
    errors = []
    for fetchname, fetcher in fetchers.items():
        try:
            fetchinst = fetcher(
                time,
                lat,
                lon,
                depth,
                magnitude,
                config=config,
                rawdir=rawdir,
                drop_non_free=drop_non_free,
                stream_collection=stream_collection,
            )
        except BaseException as e:
            fmt = 'Could not instantiate Fetcher %s, due to error\n "%s"'
            tpl = (fetchname, str(e))
            msg = fmt % tpl
            logging.warning(msg)
            errors.append(msg)
            continue
        xmin, xmax, ymin, ymax = fetchinst.BOUNDS
        if (xmin < lon < xmax) and (ymin < lat < ymax):
            instances.append(fetchinst)

    efmt = "%s M%.1f (%.4f,%.4f)"
    etpl = (time, magnitude, lat, lon)
    esummary = efmt % etpl
    streams = []
    for fetcher in instances:
        if "FDSN" in str(fetcher):
            tstreams = fetcher.retrieve_data()
            if streams:
                streams = streams + tstreams
            else:
                streams = tstreams

        else:
            events = fetcher.get_matching_events(solve=True)
            if not events:
                msg = "No event matching %s found by class %s"
                logging.warning(msg, esummary, str(fetcher))
                continue
            tstreams = fetcher.retrieve_data(events[0])
            if streams:
                streams = streams + tstreams
            else:
                streams = tstreams

        if streams is None:
            streams = []

    return (streams, errors)


def find_fetchers(lat, lon):
    """Create a dictionary of classname:class to be used in main().

    Args:
        lat (float):
            Origin latitude.
        lon (float):
            Origin longitude.

    Returns:
        dict: Dictionary of classname:class where each class is a subclass of
        shakemap.coremods.base.CoreModule.
    """

    fetchers = {}
    root = pathlib.Path(__file__).parent
    for fdir in FETCHER_DIRS:
        fetcher_path = root / fdir
        for cfile in _walk(fetcher_path):
            if str(cfile).endswith("_fetcher.py"):
                fetcher_mod = cfile
                break
        idx = max(
            loc for loc, val in enumerate(fetcher_mod.parts) if val == "gmprocess"
        )
        mod_tuple = fetcher_mod.parts[idx:]
        mod_name = ".".join(mod_tuple)
        if mod_name.endswith(".py"):
            mod_name = mod_name[:-3]
        mod = importlib.import_module(mod_name)
        for name, obj in inspect.getmembers(mod):
            if name == "DataFetcher":
                continue
            if inspect.isclass(obj) and issubclass(obj, DataFetcher):
                xmin, xmax, ymin, ymax = obj.BOUNDS
                if (xmin < lon < xmax) and (ymin < lat < ymax):
                    fetchers[name] = obj
    return fetchers
