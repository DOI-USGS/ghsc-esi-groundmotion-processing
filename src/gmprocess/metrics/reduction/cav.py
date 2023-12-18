#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third party imports
import numpy as np

# Local imports
from gmprocess.utils.constants import GAL_TO_PCTG
from gmprocess.metrics.reduction.reduction import Reduction
from gmprocess.core.stationstream import StationStream
from gmprocess.core.stationtrace import StationTrace


class CAV(Reduction):
    """Class for calculation of Cumulative Absolute Velocity."""

    def __init__(
        self,
        reduction_data,
        bandwidth=None,
        percentile=None,
        period=None,
        smoothing=None,
        interval=[5, 95],
        config=None,
    ):
        """
        Args:
            reduction_data (obspy.core.stream.Stream or numpy.ndarray):
                Intensity measurement component.
            bandwidth (float):
                Bandwidth for the smoothing operation. Default is None.
            percentile (float):
                Percentile for rotation calculations. Default is None.
            period (float):
                Period for smoothing (Fourier amplitude spectra)
                calculations. Default is None.
            smoothing (string):
                Smoothing type. Default is None.
            interval (list):
                List of length 2 with the quantiles (0-1) for duration interval
                calculation.
            config (dict):
                Config dictionary.
        """
        super().__init__(
            reduction_data=reduction_data,
            bandwidth=bandwidth,
            percentile=percentile,
            period=period,
            smoothing=smoothing,
            interval=interval,
            config=config,
        )
        self.cav_stream = None
        self.result = self.get_cav(config=config)

    def get_cav(self, config=None):
        """
        Performs calculation of cumulative absolute velocity.

        Args:
            config (dict):
                Config options.

        Returns:
            cav_intensities: Dictionary of cumulative absolute velocity for each channel.
        """
        cav_intensities = {}
        cav_stream = StationStream([], config=config)
        for trace in self.reduction_data:
            tr = trace.copy()
            # convert from cm/s/s to m/s/s
            tr.data *= 0.01
            # convert from m/s/s to g-s
            tr.data *= GAL_TO_PCTG
            # absolute value
            tr.data = abs(tr.data)

            # Calculate Cumulative Absolute Velocity
            tr.integrate(**self.config["integration"])
            cav_intensity = tr.data

            # Create a copy of stats so we don't modify original data
            stats = trace.stats.copy()
            channel = stats.channel
            stats.standard.units_type = "vel"
            stats.npts = len(cav_intensity)
            cav_stream.append(StationTrace(cav_intensity, header=stats, config=config))
            cav_intensities[channel] = np.abs(np.max(cav_intensity))
        self.cav_stream = cav_stream

        return cav_intensities
