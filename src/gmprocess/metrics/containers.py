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
        return f"ReferenceValue: {self.value:.4g}"


@dataclass(repr=False)
class Trace:
    """Class for holding StationTrace data."""

    traces: list[StationTrace]


@dataclass(repr=False)
class Scalar:
    """Class for holding scalar metric data."""

    traces: list[ReferenceValue]

    def __repr__(self):
        list_str = ", ".join([ref for ref in self.traces])
        return f"ScalarContainer({list_str})"


@dataclass(repr=False)
class CombinedScalar:
    """Class for holding combined scalar metric data."""

    trace: ReferenceValue

    def __repr__(self):
        return f"CombinedScalarContainer(trace: {self.trace})"


@dataclass(repr=False)
class FourierSpectra:
    """Class for holding Fourier Spectra metric data."""

    frequency: np.ndarray
    fourier_spectra: list[np.ndarray]


@dataclass(repr=False)
class CombinedSpectra:
    """Class for holding Fourier Spectra combined metric data."""

    frequency: np.ndarray
    fourier_spectra: np.ndarray


@dataclass(repr=False)
class Oscillator:
    """Class for holding oscillator time history for a given Container.Trace."""

    period: float
    damping: float
    oscillators: list[np.ndarray]
    oscillator_dt: float


@dataclass(repr=False)
class OscillatorCollection:
    """Class for holding a colleciton of OscillatorContainers."""

    oscillators: list[Oscillator]


@dataclass(repr=False)
class RotDTrace:
    """Class for holding traces rotated using the RotD method."""

    trace_matrix: np.ndarray
    stats: dict


@dataclass(repr=False)
class RotDOscillator:
    """Class for holding oscillator time history for a given TraceRotDContainer."""

    period: float
    damping: float
    oscillator_matrix: np.ndarray
    oscillator_dt: float


@dataclass(repr=False)
class RotDOscillatorCollection:
    """Class for holding a colleciton of OscillatorContainers."""

    oscillators: list[RotDOscillator]
