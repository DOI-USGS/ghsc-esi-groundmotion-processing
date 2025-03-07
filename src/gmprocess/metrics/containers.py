"""Module for holding dataclasses for waveform metric processing step results."""

from dataclasses import dataclass

import numpy as np

from gmprocess.core.stationtrace import StationTrace


@dataclass(repr=False)
class ReferenceValue:
    """Class for holding a scalar with supporting stats dictionary."""

    value: float
    stats: dict

    def __repr__(self):
        return f"containers.ReferenceValue(value={self.value:.4g}, stats=dict)"


@dataclass(repr=False)
class Trace:
    """Class for holding StationTrace data."""

    traces: list[StationTrace]

    def __repr__(self):
        return f"containers.Trace(traces=[StationTrace, n={len(self.traces)})"


@dataclass(repr=False)
class Scalar:
    """Class for holding scalar metric data."""

    values: list[ReferenceValue]

    def __repr__(self):
        return f"containers.Scalar(values=[ReferenceValue, n={len(self.values)}])"


@dataclass(repr=False)
class CombinedScalar:
    """Class for holding combined scalar metric data."""

    value: ReferenceValue

    def __repr__(self):
        return "containers.CombinedScalar(value=ReferenceValue)"


@dataclass(repr=False)
class FourierSpectra:
    """Class for holding Fourier Spectra metric data."""

    frequency: np.ndarray
    fourier_spectra: list[np.ndarray]
    stats_list: list[dict]

    def __repr__(self):
        return (
            "containers.FourierSpectra(\n"
            f"  frequency=ndarray {self.frequency.shape},\n"
            f"  fourier_spectra=[ndarray, n={len(self.fourier_spectra)}]\n"
            f"  stats_list=[dict, n={len(self.stats_list)}],\n"
            ")"
        )


@dataclass(repr=False)
class CombinedSpectra:
    """Class for holding Fourier Spectra combined metric data."""

    frequency: np.ndarray
    fourier_spectra: np.ndarray

    def __repr__(self):
        return (
            "containers.CombinedSpectra(\n"
            f"  frequency=ndarray, {self.frequency.shape}\n"
            f"  fourier_spectra=ndarray {self.fourier_spectra.shape}\n"
            ")"
        )


@dataclass(repr=False)
class Oscillator:
    """Class for holding oscillator time history for a given trace.

    The 'oscillators' list maps to traces within the StationStream.
    """

    period: float
    damping: float

    # Total acceleration
    acceleration: list[np.ndarray]

    # Relative velocity
    velocity: list[np.ndarray]

    # Relative displacement
    displacement: list[np.ndarray]

    oscillator_dt: float
    stats_list: list[dict]

    def __repr__(self):
        return (
            "containers.Oscillator(\n"
            f"  period={self.period},\n"
            f"  damping={self.damping},\n"
            f"  acceleration=[nd.array, n={len(self.acceleration)}],\n"
            f"  velocity=[nd.array, n={len(self.velocity)}],\n"
            f"  displacement=[nd.array, n={len(self.displacement)}],\n"
            f"  stats_list=[dict, n={len(self.stats_list)}],\n"
            ")"
        )


@dataclass(repr=False)
class SpectralAcceleration:
    """Class for holding spectral acceleration results for a given StationStream.

    The 'results' list maps to traces within the StationStream.
    """

    results: list[float]
    stats_list: list[dict]

    def __repr__(self):
        return (
            "containers.SpectralAcceleration(\n"
            f"  results=[float, n={len(self.results)}],\n"
            f"  stats_list=[dict, n={len(self.stats_list)}],\n"
            ")"
        )


@dataclass(repr=False)
class RotDTrace:
    """Class for holding traces rotated using the RotD method."""

    matrix: np.ndarray
    stats: dict

    def __repr__(self):
        return (
            "containers.RotDTrace(\n"
            f"  matrix=ndarray {self.matrix.shape}],\n"
            "  stats=dict,\n"
            ")"
        )


@dataclass(repr=False)
class RotDOscillator:
    """Class for holding oscillator time history for a given TraceRotDContainer."""

    period: float
    damping: float
    acceleration_matrix: np.ndarray
    velocity_matrix: np.ndarray
    displacement_matrix: np.ndarray
    oscillator_dt: float
    stats: dict

    def __repr__(self):
        return (
            "containers.RotDOscillator(\n"
            f"  period={self.period},\n"
            f"  damping={self.damping},\n"
            f"  acceleration_matrix=ndarray {self.acceleration_matrix.shape}],\n"
            f"  velocity_matrix=ndarray {self.velocity_matrix.shape}],\n"
            f"  displacement_matrix=ndarray {self.displacement_matrix.shape}],\n"
            f"  oscillator_dt={self.oscillator_dt},\n"
            "  stats=dict,\n"
            ")"
        )


@dataclass(repr=False)
class RotDMax:
    """Class for holding oscillator time history for a given TraceRotDContainer."""

    period: float
    damping: float
    oscillator_maxes: np.ndarray
    stats: dict
    type: str

    def __repr__(self):
        return (
            "containers.RotDMax(\n"
            f"  period={self.period},\n"
            f"  damping={self.damping},\n"
            f"  oscillator_maxes=ndarray {self.oscillator_maxes.shape},\n"
            "  stats=dict,\n"
            f"  type={self.type}\n"
            ")"
        )


@dataclass(repr=False)
class RotD:
    """Class for holding oscillator time history for a given TraceRotDContainer."""

    period: float
    damping: float
    percentile: float
    value: ReferenceValue

    def __repr__(self):
        return (
            "containers.RotD(\n"
            f"  period={self.period},\n"
            f"  damping={self.damping},\n"
            f"  percentile={self.percentile},\n"
            "  value=ReferenceValue,\n"
            ")"
        )
