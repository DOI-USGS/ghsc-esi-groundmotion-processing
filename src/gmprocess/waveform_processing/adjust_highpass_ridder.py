"""Module for the ridder_fchp processign step."""

import inspect
import numpy as np

from esi_core.gmprocess.waveform_processing.auto_fchp import get_fchp
from gmprocess.waveform_processing.taper import taper
from gmprocess.waveform_processing.filtering import highpass_filter
from gmprocess.waveform_processing.processing_step import processing_step

FORDER = 5.0


@processing_step
def ridder_fchp(st, target=0.02, tol=0.001, maxiter=30, maxfc=0.5, same_horiz=True, config=None):
    """Search for highpass corner using Ridder's method.

    Search such that the criterion that the ratio between the maximum of a third order
    polynomial fit to the displacement time series and the maximum of the displacement
    timeseries is a target % within a tolerance.

    This algorithm searches between a low initial corner frequency a maximum fc.

    Method developed originally by Scott Brandenberg

    Args:
        st (StationStream):
            Stream of data.
        target (float):
            target percentage for ratio between max polynomial value and max
            displacement.
        tol (float):
            tolerance for matching the ratio target
        maxiter (float):
            maximum number of allowed iterations in Ridder's method
        maxfc (float):
            Maximum allowable value of the highpass corner freq.
        int_method (string):
            method used to perform integration between acceleration, velocity, and
            dispacement. Options are "frequency_domain", "time_domain_zero_init" or
            "time_domain_zero_mean"
        same_horiz (bool):
            impose same highpass corner frequency across horizontal components
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: Stream with the highpass corner adjusted using Ridder's method.
    """
    if not st.passed:
        return st

    hp_sig = inspect.signature(highpass_filter)
    frequency_domain = hp_sig.parameters["frequency_domain"].default

    taper_sig = inspect.signature(taper)
    taper_width = taper_sig.parameters["width"].default

    if frequency_domain:
        filter_code = 1
    else:
        filter_code = 0

    adjusted_horiz_hp = False
    for tr in st:
        if tr.stats.standard.units_type != "acc":
            tr.fail("Unit type must be acc to apply Ridder fchp method.")
            continue

        if not tr.passed:
            continue
        initial_corners = tr.get_parameter("corner_frequencies")
        if initial_corners["type"] == "reviewed":
            continue

        initial_f_hp = initial_corners["highpass"]

        new_f_hp = get_fchp(
            dt=tr.stats.delta,
            acc=tr.data,
            target=target,
            tol=tol,
            poly_order=FORDER,
            maxiter=maxiter,
            tukey_alpha=taper_width,
            fchp_max=maxfc,
            filter_type=filter_code,
        )

        # Method did not converge if new_f_hp reaches maxfc
        if (maxfc - new_f_hp) < 1e-9:
            tr.fail("auto_fchp did not find an acceptable f_hp.")
            continue

        if new_f_hp > initial_f_hp:
            adjusted_horiz_hp = True if tr.is_horizontal else adjusted_horiz_hp
            tr.set_parameter(
                "corner_frequencies",
                {
                    "type": "snr_polyfit",
                    "highpass": new_f_hp,
                    "lowpass": initial_corners["lowpass"],
                },
            )

    if adjusted_horiz_hp and same_horiz and st.passed and st.num_horizontal > 1:
        hp_corners = [
            tr.get_parameter("corner_frequencies")["highpass"]
            for tr in st if tr.is_horizontal
        ]
        hp_corner = np.max(hp_corners)
        for tr in st:
            if tr.is_horizontal:
                cfdict = tr.get_parameter("corner_frequencies")
                cfdict["highpass"] = hp_corner
                tr.set_parameter("corner_frequencies", cfdict)
    return st
