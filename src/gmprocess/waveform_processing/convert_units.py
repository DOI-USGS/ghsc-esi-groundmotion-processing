"""Module for converting units."""

from gmprocess.waveform_processing.processing_step import processing_step


@processing_step
def convert_to_acceleration(
    st, taper=True, taper_type="hann", taper_width=0.05, taper_side="both", config=None
):
    """Convert stream to acceleration if it isn't acceleration.

    Args:
        st (StationStream):
            Stream of data.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: Stream in units of acceleration.
    """
    current_units = st[0].stats.standard.units_type
    if current_units == "acc":
        return st

    for tr in st:
        if taper:
            tr.taper(max_percentage=taper_width, type=taper_type, side=taper_side)
        diff_conf = config["differentiation"]
        tr.differentiate(frequency=diff_conf["frequency"])
    return st
