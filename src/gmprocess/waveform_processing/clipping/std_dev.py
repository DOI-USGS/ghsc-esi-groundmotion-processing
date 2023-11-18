"""Module for the standard devation test for clipping detection."""

import numpy as np
from gmprocess.waveform_processing.clipping.clip_detection import ClipDetection


class StdDev(ClipDetection):
    """
    Class for the standard deviation clipping detection algorithm.

    Attributes:
        st (StationStream):
            Record of three orthogonal traces.
        test_all (bool, default=False):
            If true, compute and store number of outlying points for
            all traces.
        is_clipped (bool):
            True if the record is clipped.
        amp_thresh (float, default=0.85):
            Threshold for maximum/minimum amplitude of trace.
        n_std (int, default=12):
            Number of neighboring points to calculate std dev with.
        std_thresh (float, default=0.001):
            Maximum threshold for std dev.
        point_thresh (int, default=5):
            Threshold number of points below std_thresh.
        num_outliers (int/list):
            The number of points exceeding the std dev threshold for the
            first clipped trace or list of number of points for each
            trace (if test_all=True).

    Methods:
        See parent class.
    """

    def __init__(
        self,
        st,
        amp_thresh=0.85,
        n_std=12,
        std_thresh=0.001,
        point_thresh=5,
        test_all=False,
    ):
        """
        Constructs all neccessary attributes for the StdDev class.

        Args:
            st (StationStream):
                Record of three orthogonal traces.
            test_all (bool, default=False):
                If true, compute and store number of outlying points for
                all traces.
            amp_thresh (float, default=0.85):
                Threshold for maximum/minimum amplitude of trace.
            n_std (int, default=12):
                Number of neighboring points to calculate std dev with.
            std_thresh (float, default=0.001):
                Maximum threshold for std dev.
            point_thresh (int, default=5):
                Threshold number of points exceeding std_thresh.
        """
        ClipDetection.__init__(self, st.copy(), test_all)
        self.amp_thresh = amp_thresh
        self.n_std = n_std
        self.std_thresh = std_thresh
        self.point_thresh = point_thresh
        if self.test_all:
            self.num_outliers = []
        else:
            self.num_outliers = None
        self._get_results()

    def _clean_trace(self, tr):
        """
        Helper function to clean the trace

        Args:
            tr (StationTrace):
                A single trace in the record.

        Returns:
            clean_tr (StationTrace):
                Cleaned trace.
        """
        clean_tr = tr.copy()
        clean_tr.detrend(type="constant")
        clean_tr.normalize()
        return clean_tr

    def _detect(self, tr):
        """
        For all points with amplitude greater than amp_thresh, calculate
        standard deviation (std) of the n_std neighboring points. Fail the
        trace if the std of n_std neighboring points is less than std_thresh
        for any point_thresh points.

        Args:
            tr (StationTrace):
                A single trace in the record.

        Returns:
            bool:
                Is the trace clipped?
        """
        tr_std = tr.copy()
        tr_std.data = np.zeros(len(tr.data))
        thresh_max = self.amp_thresh * np.max(tr.data)
        thresh_min = self.amp_thresh * np.min(tr.data)
        for i in range(len(tr.data) - self.n_std):
            tr_std.data[i] = np.std(tr.data[i : i + self.n_std])
        (i_lowstd,) = np.where(
            (tr_std.data < self.std_thresh)
            & ((tr.data >= thresh_max) | (tr.data <= thresh_min))
        )
        num_outliers = len(i_lowstd)
        if self.test_all:
            self.num_outliers.append(num_outliers)
        else:
            self.num_outliers = num_outliers
        if num_outliers > self.point_thresh:
            return True
        return False
