import numpy as np
import pytest

from gmprocess.waveform_processing.prism_adaptive_baseline import (
    prism_adaptive_baseline,
    prism_quality_criteria,
)
from gmprocess.waveform_processing.windows import signal_split
from gmprocess.waveform_processing.corner_frequencies import get_corner_frequencies


def test_prism_quality_criteria(load_data_us1000778i, config):
    streams, event = load_data_us1000778i
    streams = streams.copy()
    stream = streams[0]

    with pytest.raises(ValueError):
        stream = prism_quality_criteria(stream, config=config)
    stream = signal_split(stream, event)
    with pytest.raises(ValueError):
        stream = prism_quality_criteria(stream, config=config)
    stream = get_corner_frequencies(stream, event, method="magnitude")
    stream = prism_quality_criteria(stream, config=config)


def test_prism_adaptive_baseline(load_data_us1000778i, config):
    streams, event = load_data_us1000778i
    streams1 = streams.copy()
    stream1 = streams1[0]

    stream1 = signal_split(stream1, event)
    stream1 = get_corner_frequencies(stream1, event, method="magnitude")
    stream1 = prism_adaptive_baseline(stream1, config=config)
    stream2 = stream1.copy()

    # With default parameters, this record passes QA and no baseline correction is
    # applied
    final_accel = []
    for trace in stream1:
        detrend_doc = trace.provenance.provenance_list[-1]
        assert detrend_doc["prov_id"] == "detrend"
        assert (
            detrend_doc["prov_attributes"]["detrending_method"]
            == "PRISM adaptive baseline correction passsed QA"
        )
        final_accel.append(trace.data[-1])
    np.testing.assert_allclose(final_accel, [0.370, -0.68, 0.12])

    # Now lower the trailing velocity threshld until it fails
    stream2 = prism_adaptive_baseline(
        stream2, n_iter=20, trail_vel_threshold=0.001, config=config
    )
    final_accel = []
    for trace in stream2:
        detrend_doc = trace.provenance.provenance_list[-1]
        assert detrend_doc["prov_id"] == "detrend"
        assert (
            detrend_doc["prov_attributes"]["detrending_method"]
            == "PRISM adaptive baseline correction applied"
        )
        final_accel.append(trace.data[-1])
    np.testing.assert_allclose(
        final_accel, [0.28856560674991816, -0.9142479198374542, 0.17449313058250204]
    )
