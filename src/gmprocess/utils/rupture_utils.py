"""Module for utilities related to the rupture file."""

from gmprocess.utils.constants import RUPTURE_FILE


def get_rupture_filename(event_dir):
    """Get the path to the rupture file, or None if there is not rupture file.

    Args:
        event_dir (pathlib.Path):
            Event directory.

    Returns:
        str: Path to the rupture file. Returns None if no rupture file exists.
    """
    filename = event_dir / RUPTURE_FILE
    if not filename.is_file():
        filename = None
    return filename
