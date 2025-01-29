"""Module for the ping test for clipping detection."""

import numpy as np
from gmprocess.waveform_processing.clipping.clip_detection import ClipDetection


class Ping(ClipDetection):
    """
    Class for the ping clipping detection algorithm.

    Attributes:
        st (StationStream):
            Record of three orthogonal traces.
        test_all (bool, default=False):
            If true, compute and store number of outlying points for
            all traces.
        is_clipped (bool):
            True if the record is clipped.
        percent_thresh (float, default=0.57):
            Percent of data range serving as a multiplicative factor
            to determine ping threshold.
        num_outliers (int/list):
            The number of points with difference exceeding threshold
            in the first clipped trace or list of number of points for
            each trace (if test_all=True).

    Methods:
       See parent class.
    """

    def __init__(self, st, percent_thresh=0.57, test_all=False):
        """
        Constructs all necessary attributes for the Ping class.

        Args:
            st (StationStream):
                Record of three orthogonal traces.
            percent_thresh (float, default=0.57):
                Percent of data range serving as a multiplicative factor
                to determine ping threshold.
            test_all (bool, default=False):
                If true, compute and store number of outlying points for
                all traces.
        """
        ClipDetection.__init__(self, st.copy(), test_all)
        self.percent_thresh = percent_thresh
        self.num_outliers = []
        self.abs_diff = None
        self.threshold = None
        self._get_results()

    def _detect(self, clip_tr):
        """
        If any two points differ by more than a threshold, fail the trace.
        Threshold given as percent_thresh * data-range.

        Args:
            clip_tr (StationTrace):
                A single trace in the record.

        Returns:
            bool:
                Is the trace clipped?
        """
        data_range = np.abs(np.max(clip_tr.data)) - np.min(clip_tr.data)
        self.abs_diff = np.abs(np.diff(clip_tr))
        self.threshold = self.percent_thresh * data_range
        points_outlying = np.where(self.abs_diff > self.threshold)[0]
        num_outliers = len(points_outlying)
        self.num_outliers.append(num_outliers)
        if np.any(num_outliers > 0):
            return True
        return False
