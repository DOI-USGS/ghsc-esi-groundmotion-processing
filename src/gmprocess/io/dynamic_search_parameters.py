"""Module for computing dynamic search parameters for an earthquake."""

import copy
import numpy as np
from scipy.interpolate import interp1d

from openquake.hazardlib.imt import PGA

from gmprocess.utils.ground_motion_models import load_model

REGION_PROB_KEYS = {
    "ActiveShallow": "ProbabilityActiveShallow",
    "ActiveDeep": "ProbabilityActiveDeep",
    "VolcanicShallow": "ProbabilityVolcanic",
    "SubductionIntraslab": "ProbabilitySubductionIntraslab",
    "SubductionInterface": "ProbabilitySubductionInterface",
    "SubductionCrustal": "ProbabilitySubductionCrustal",
    "StableShallow": "ProbabilityStableShallow",
}

# Assumed inputs for GMMs
VS30 = 300.0
VS30MEASURED = False
RAKE = 90.0
Z1PT0 = 100.0  # meters
Z2PT5 = 200.0  # meters
ZTOR = 0.0
DIP = 90.0
HYPO_DEPTH = 2.0


class SearchParameters(object):
    """Class for sorting out dynamic search parameters."""

    def __init__(self, magnitude, config, strec=None):
        """Initialize SearchParamters object.

        Args:
            magnitude (float):
                Earthquake magnitude.
            config (dict):
                Config dictionary.
            strec (STREC):
                A STREC object.
        """
        self.magnitude = magnitude
        self.config = copy.deepcopy(config)
        self.strec = copy.deepcopy(strec)
        self.duration = None
        self._compute_duration()
        self.distance = None
        self._compute_distance()

    def _compute_duration(self):
        dpars = self.config["fetchers"]["search_parameters"]["duration"]
        self.duration = dpars["c0"] + dpars["c1"] * self.magnitude
        if self.strec is None:
            return
        tect_reg = self.strec.results["TectonicRegion"]
        if tect_reg not in dpars:
            return
        self.duration = dpars[tect_reg]["c0"] + dpars[tect_reg]["c1"] * self.magnitude

    def _compute_distance(self):
        dpars = self.config["fetchers"]["search_parameters"]["distance"]
        if self.strec is not None:
            strec_dict = self.strec.results
            region_probabilities = []
            regions = []
            for region, strec_prob in REGION_PROB_KEYS.items():
                regions.append(region)
                region_probabilities.append(strec_dict[strec_prob])

            selected_region = regions[np.argmax(region_probabilities)]
            selected_model_name = self.config["gmm_selection"][selected_region]
        else:
            # Use StableShallow as the conservative choice
            selected_model_name = self.config["gmm_selection"]["StableShallow"]
        selected_model = load_model(selected_model_name)
        pga_threshold = dpars["pga"]

        # Setup recarrays
        npts = 300
        ctx = np.recarray(
            npts,
            dtype=np.dtype(
                [
                    ("mag", float),
                    ("vs30", float),
                    ("vs30measured", bool),
                    ("z1pt0", float),
                    ("z2pt5", float),
                    ("ztor", float),
                    ("hypo_depth", float),
                    ("dip", float),
                    ("rake", float),
                    ("width", float),
                    ("rrup", float),
                    ("rjb", float),
                    ("rx", float),
                    ("ry0", float),
                ]
            ),
        )
        ctx["mag"] = self.magnitude
        ctx["vs30"] = VS30
        ctx["vs30measured"] = VS30MEASURED
        ctx["z1pt0"] = Z1PT0
        ctx["ztor"] = Z2PT5
        ctx["hypo_depth"] = HYPO_DEPTH
        ctx["dip"] = DIP
        ctx["rake"] = RAKE
        width_wc94 = 10 ** (-1.01 + 0.32 * self.magnitude)
        ctx["width"] = width_wc94
        distance = np.logspace(1, np.log10(dpars["max_distance"]), npts)
        ctx["rrup"] = distance
        ctx["rjb"] = distance
        ctx["rx"] = distance
        ctx["ry0"] = distance

        mean = np.zeros([1, npts])
        sigma = np.zeros_like(mean)
        tau = np.zeros_like(mean)
        phi = np.zeros_like(mean)
        selected_model.compute(ctx, [PGA()], mean, sigma, tau, phi)
        interp = interp1d(
            mean.flatten(),
            distance,
            bounds_error=False,
            fill_value=(distance[-1], distance[0]),
        )
        self.distance = interp(np.log(pga_threshold))
