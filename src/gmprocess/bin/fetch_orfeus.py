import copy
import importlib.metadata
import io
import json
import logging
import pathlib

import gmprocess.utils.config as gmconfig
import h5py
import numpy
import obspy
import requests
from gmprocess.core.provenance import LabelProvenance


class App:
    """Download from the ORFEUS Engineering Strong Motion data center as ASDF files.

    The resulting ASDF files contain data that can be used to compute station and
    waveform metrics. A user does not run the gmprocess subcommands 'download',
    'assemble', or 'process_waveforms'.
    """

    def initialize(
        self,
        catalog: str,
        event_ids: list,
        processing_label: str,
        data_dir: str = "data-waveforms/orfeus",
    ):
        """Initialize the application.

        Args:
            catalog (str):
                Catalog associated with event ids.
            event_ids (list):
                List of event ids to query for event data.
            processing_label (str):
                Type of ORFEUS processing and label to use for waveforms in gmprocess.
            data_dir (str):
                Name of directory for holding event data.
        """
        self.catalog = catalog
        self.queue = event_ids
        self.processing_label = processing_label
        self.data_dir = pathlib.Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def main(
        self,
        fetch_waveforms: bool = True,
        to_gmprocess: bool = True,
        resume: str = None,
    ):
        """Application driver.

        Args;
            fetch_waveforms (bool):
                Fetch event data from ORFEUS.
            to_gmprocess (bool):
                Make downloaded ASDF files compatible with gmprocess.
            resume (str):
                Event id to start with.
        """
        i_start = self._get_start(resume)
        num_events = len(self.queue)
        for i_event, event_id in enumerate(self.queue[i_start:]):
            logging.info(
                f"Working on {event_id} ({i_start + i_event + 1} of {num_events})..."
            )

            if fetch_waveforms:
                self.fetch_waveforms(event_id)
            if to_gmprocess:
                self.to_gmprocess(event_id)

    def fetch_waveforms(self, event_id):
        """Fetch event data from ORFEUS.

        Args:
            event_id (str):
                Event id for fetching event data.
        """
        logging.info(f"Fetching event data for {event_id}...")

        url = (
            f"https://esm-db.eu/esmws/eventdata/1/query?"
            f"eventid={event_id}&catalog={self.catalog}&"
            f"format=hdf5&processing-type={self.processing_label}&"
            "add-xml=True"
        )
        response = requests.get(url)
        if response.status_code == 204:
            logging.info(
                (
                    f"No event data found for {event_id}. "
                    "Maybe try changing the processing-type."
                )
            )
            return
        self._write_raw_content(event_id, response)

    def to_gmprocess(self, event_id):
        """Make ASDF file downloaded from ORFEUS compatible with gmprocess.

        Args:
            event_id (str):
                Event id for fetching event data.
        """
        filename = self.data_dir / event_id / "workspace.h5"
        if not filename.exists():
            logging.debug(
                (
                    f"Skipping updating workspace file for {event_id}. "
                    f"File {filename} not found."
                )
            )
            return

        logging.info(
            (
                f"Updating workspace file for {event_id} to conform "
                "to gmprocess requirements..."
            )
        )
        config = gmconfig.get_config()
        workspace = Workspace(filename, event_id)
        # streams = workspace.get_streams()
        workspace.add_provenance(self.processing_label, config)
        workspace.add_config(config)
        workspace.update_event_id()
        workspace.update_tags(self.processing_label)

    def _get_start(self, resume):
        """Get index in list of event ids corresponding to event 'resume'.

        Args:
            resume (str):
                Event id to find in list of event ids.
        Returns:
            Index (int) in list of event ids to start with.
        """
        start = 0
        if resume:
            start = self.queue.index(resume)
            if not start:
                raise ValueError(
                    f"Could not find earthquake '{resume}' to resume workflow."
                )
        return start

    def _write_raw_content(self, event_id, response):
        """Write raw content to workspace file for event 'event_id'.

        Args:
            event_id (str):
                Event id associated with content.
            response (requests.Response):
                Response returned by requests.get().
        """
        event_dir = self.data_dir / event_id
        event_dir.mkdir(exist_ok=True)
        filename = event_dir / "workspace.h5"
        with open(filename, "wb") as fout:
            for chunk in response.iter_content(chunk_size=1024):
                fout.write(chunk)


class Workspace:
    """Local object for operations on workspace (ASDF) file."""

    def __init__(self, filename: str, event_id: str):
        """Constructor.

        Args:
            filename (str):
                Name of workspace file.
            event_id (str):
                Event id.
        """
        self.h5 = h5py.File(filename, "a")
        self.event_id = event_id

    def add_config(self, config: dict):
        """Add gmprocess config to workspace.

        Args:
            config (dict):
                gmprocess configuration.
        """
        CONFIG_PATH = "/AuxiliaryData/config/config"

        config_bytes = json.dumps(config).encode("utf-8")
        config_array = numpy.frombuffer(config_bytes, dtype=numpy.uint8)
        self.h5.create_dataset(CONFIG_PATH, data=config_array)

    def update_event_id(self):
        """Set id in QuakeML to 'event_id'."""
        earthquakes = obspy.read_events(io.BytesIO(self.h5["QuakeML"][:]))

        earthquakes[0].resource_id = obspy.core.event.resourceid.ResourceIdentifier(
            self.event_id
        )
        io_buffer = io.BytesIO()
        earthquakes.write(io_buffer, format="QuakeML")
        self._update_dataset_from_buffer(self.h5["QuakeML"], io_buffer)

    def update_tags(self, processing_label: str):
        """Update waveform tags to match gmprocess convention.

        gmprocess convention for tag is '{event_id}_{processing_label}'.

        Args:
            processing_label (str):
                Processing label for waveforms.
        """
        for st_id, group in self.h5["Waveforms"].items():
            group_keys = [key for key in group.keys()]
            for key in group_keys:
                if key == "StationXML":
                    continue
                seed_id, start, end, old_tag = key.split("__")
                new_tag = self._new_tag(self.event_id, processing_label)
                new_key = "__".join((seed_id, start, end, new_tag))
                group.move(key, new_key)

    def add_provenance(self, processing_label: str, config: dict):
        """Add basic provenance information for processed waveforms.

        Args:
            processing_label (str):
                Processing label for waveforms.
            config (dict):
                gmprocess configuration.
        """
        gmprocess_version = importlib.metadata.version("gmprocess")
        label_prov = LabelProvenance(
            label=processing_label, gmprocess_version=gmprocess_version, config=config
        )
        label_provdoc = label_prov.provenance_document
        label_provdoc.entity(
            "seis_prov:sp000_sa_orfeus",
            other_attributes=(
                ("prov:label", "ORFEUS ESM"),
                ("seis_prov:website", "https://esm-db.eu/"),
                ("seis_prov:doi", "10.1785/0220150278"),
            ),
        )

        for st_id, group in self.h5["Waveforms"].items():
            group_keys = [key for key in group.keys()]
            for key in group_keys:
                if key == "StationXML":
                    continue

                seed_id, start, end, old_tag = key.split("__")
                new_tag = self._new_tag(self.event_id, processing_label)
                trace_id = f"{seed_id}_{new_tag}"
                identifier = f"seis_prov:sp001_wf_{trace_id.lower()}"
                prov_doc = copy.deepcopy(label_provdoc)
                trace_prov = prov_doc.entity(
                    identifier,
                    other_attributes=(
                        ("prov:label", "Waveform Trace"),
                        ("prov:type", "seis_prov:waveform_trace"),
                        ("seis_prov:seed_id", seed_id),
                    ),
                )
                processing = prov_doc.activity(
                    "seis_prov:sp001_rr_000001",
                    other_attributes=(
                        ("prov:label", "Mannual Processing"),
                        ("prov:type", "seis_prov:remove_response"),
                    ),
                )

                with io.BytesIO() as io_buffer:
                    prov_doc.serialize(io_buffer, format="xml")
                    data = self._buffer_to_dataset(io_buffer)
                self.h5["Provenance"].create_dataset(trace_id, data=data)

    @staticmethod
    def _new_tag(event_id: str, processing_label: str):
        return f"{event_id}_{processing_label}"

    @staticmethod
    def _update_dataset_from_buffer(dataset, io_buffer: bytes):
        data = Workspace._buffer_to_dataset(io_buffer)
        dataset.resize(data.shape)
        dataset[:] = data

    @staticmethod
    def _buffer_to_dataset(io_buffer: bytes):
        io_buffer.seek(0)
        data = numpy.frombuffer(io_buffer.read(), dtype=numpy.byte)
        return data


def cli():
    """Command line interface to application for fetching event data from ORFEUS."""
    import argparse

    DESCRIPTION = (
        "Application for fetching event data from "
        "ORFEUS Engineering Strong Motion Database."
    )

    parser = argparse.ArgumentParser(
        description=DESCRIPTION, formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--processing-type",
        action="store",
        dest="processing_type",
        required=True,
        choices=["CV", "AP", "MP"],
        help="ORFEUS processing type",
    )
    parser.add_argument(
        "--event-catalog",
        action="store",
        dest="event_catalog",
        default="USGS",
        choices=["ESM", "EMSC", "USGS", "ISC", "INGV"],
        help="Catalog for events",
    )
    parser.add_argument(
        "--data-dir",
        action="store",
        dest="data_dir",
        default="data-waveforms/orfeus",
        help="Root directory for event data.",
    )

    events_group = parser.add_mutually_exclusive_group(required=True)
    events_group.add_argument(
        "--events-filename",
        action="store",
        dest="events_filename",
        help="Filename containing list of event ids, one per line",
    )
    events_group.add_argument(
        "--event-ids",
        action="store",
        dest="event_ids",
        help="Comma separated list of event ids",
    )

    parser.add_argument(
        "--fetch-waveforms",
        action="store_true",
        dest="fetch_waveforms",
        help="Fetch ASDF files for events from ORFEUS ESM",
    )
    parser.add_argument(
        "--to-gmprocess",
        action="store_true",
        dest="to_gmprocess",
        help="Adjust ASDF file for compatibility with gmprocess",
    )

    parser.add_argument("--debug", action="store_true", dest="debug")
    parser.add_argument(
        "--resume",
        action="store",
        dest="resume",
        metavar="EVENT_ID",
        help="Resume processing at event EVENT_ID",
    )

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if args.event_ids:
        event_ids = args.event_ids.split(",")
    elif args.events_filename:
        with open(args.events_filename) as fin:
            event_ids = fin.read().split()
    else:
        raise ValueError("Internal error. No events specified.")

    app = App()
    app.initialize(
        catalog=args.event_catalog,
        event_ids=event_ids,
        processing_label=args.processing_type,
        data_dir=args.data_dir,
    )
    app.main(fetch_waveforms=args.fetch_waveforms, to_gmprocess=args.to_gmprocess)


if __name__ == "__main__":
    cli()
