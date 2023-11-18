"""Module for individual/heuristic clipping methods. These get combined with the
neurual network model (clipping_ann.py). The NN model gets called by clipping_check.py
module."""

import numpy as np


class ClipDetection:
    """
    Parent class for clipping detection algorithms.

    Attributes:
        st (StationStream):
            Record of three orthogonal traces.
        test_all (bool, default=False):
            If true, compute test values for all traces.
        is_clipped (bool):
            True if the record is clipped.

    Methods:
        _detect():
            Determines if the trace is clipped or not.
        _clean_trace():
            Trim and normalize a trace.
        _get_results():
            Iterates through and runs _detect() on each trace in the stream.
    """

    def __init__(self, st, test_all=False):
        """
        Constructs all neccessary attributes for the ClipDetection method
        object.

        Args:
            st (StationStream):
                Stream of data.
            test_all (bool, default=False):
                If true, compute test values for all traces.
        """
        self.st = st.copy()
        self.is_clipped = False
        self.test_all = test_all

    def _clean_trace(self, tr):
        """
        Helper function to clean the trace. This is a no-op unless overwritten by child
        class.

        Args:
            tr (StationTrace):
                A single trace in the record.

        Returns:
            clean_tr (StationTrace):
                Cleaned trace.
        """
        return tr

    def _trim_trace(self, tr):
        """
        Trim the trace to chop off the tail.

        Args:
            tr (StationTrace):
                A single trace in the record.

        Returns:
            clean_tr (StationTrace):
                Cleaned trace.
        """
        data_abs = np.abs(tr.data)
        data_abs_max = np.max(data_abs)
        idx_remove = np.where(data_abs < (0.05 * data_abs_max))[0]
        idiff = np.diff(idx_remove)
        last_index = len(tr.data)
        for idx, idx_diff in zip(np.flip(idx_remove), np.flip(idiff)):
            if idx_diff > 1:
                last_index = idx
                break
        clean_tr = tr.copy()
        clean_tr.data = clean_tr.data[:last_index]
        return clean_tr

    def _detect(self, clip_tr):
        """
        Clipping detection algorithm for the individual child class

        Args:
            clip_tr (StationTrace):
                A single trace in the record.

        Returns:
            bool:
                Did the trace pass the test?
        """
        return False

    def _get_results(self):
        """
        Iterates through and runs _detect() on each trace in the stream to
        determine if the record is clipped or not.

        Args:
            None

        Returns:
            None
        """
        for tr in self.st:
            tr = self._trim_trace(tr)
            tr = self._clean_trace(tr)
            temp_is_clipped = self._detect(tr)
            if temp_is_clipped:
                self.is_clipped = temp_is_clipped
                if self.test_all:
                    continue
                else:
                    break
