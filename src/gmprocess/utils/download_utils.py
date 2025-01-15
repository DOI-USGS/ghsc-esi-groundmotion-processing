"""Module for download unility functions."""

# stdlib imports
import sys
import json
import logging

# third party imports
import requests

# local imports
from gmprocess.utils import constants
from gmprocess.utils.strec import STREC

TIMEFMT2 = "%Y-%m-%dT%H:%M:%S.%f"


FLOAT_PATTERN = r"[-+]?[0-9]*\.?[0-9]+"

EVENT_TEMPLATE = (
    "https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/[EVENT].geojson"
)


def download_comcat_event(event_id):
    """Download event data from ComCat as GeoJSON.

    Args:
        event_id (str):
            ComCat event id.
    Returns:
        Dictionary with event information.
    """
    event_url = EVENT_TEMPLATE.replace("[EVENT]", event_id)
    response = requests.get(event_url)
    if response.ok:
        return response.json()
    else:
        logging.info(f"{event_id} not found in ComCat.")
        sys.exit(1)


def download_rupture_file(event_id, event_dir):
    """Download rupture file from ComCat.

    Args:
        event_id (str):
            Event id.
        event_dir (pathlib.Path):
            Event directory.
    """
    try:
        data = download_comcat_event(event_id)
    except:
        logging.info(
            f"{event_id} is not in Comcat and so we cannot get a rupture.json file."
        )
        return
    try:
        shakemap_prod = data["properties"]["products"]["shakemap"][0]
        rupture_url = shakemap_prod["contents"]["download/rupture.json"]["url"]
        rupture_filename = event_dir / constants.RUPTURE_FILE
        response = requests.get(rupture_url)
        logging.info(f"Created rupture file: {rupture_filename}")
        with open(rupture_filename, "wt", encoding="utf-8") as fout:
            json.dump(response.json(), fout)
    except BaseException:
        logging.info(f"{event_id} does not have a rupture.json file.")


def get_strec_results(event, event_dir):
    strec_file = event_dir / constants.STREC_FILE
    if strec_file.exists():
        logging.info(f"Reading in strec file: {strec_file}")
        strec = STREC.from_file(strec_file)
    else:
        logging.info(f"Created strec file: {strec_file}")
        strec = STREC.from_event(event)
        strec.to_file(strec_file)
    return strec
