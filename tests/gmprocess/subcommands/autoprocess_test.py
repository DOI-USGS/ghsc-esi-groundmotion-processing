import os

from gmprocess.utils import constants
from gmprocess.utils import tests_utils
from gmprocess.apps.gmrecords import GMrecordsApp


def test_autoprocess():
    EVENT_ID = "ci38457511"
    WORKSPACE_ITEMS = (
        "AuxiliaryData",
        "AuxiliaryData/Cache",
        "AuxiliaryData/Cache/EventSpectrumFreq",
        "AuxiliaryData/Cache/EventSpectrumFreq/CI.CCC",
        "AuxiliaryData/Cache/EventSpectrumFreq/CI.CCC/CI.CCC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/EventSpectrumFreq/CI.CCC/CI.CCC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/EventSpectrumFreq/CI.CCC/CI.CCC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/EventSpectrumFreq/CI.CLC",
        "AuxiliaryData/Cache/EventSpectrumFreq/CI.CLC/CI.CLC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/EventSpectrumFreq/CI.CLC/CI.CLC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/EventSpectrumFreq/CI.CLC/CI.CLC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/EventSpectrumFreq/CI.TOW2",
        "AuxiliaryData/Cache/EventSpectrumFreq/CI.TOW2/CI.TOW2.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/EventSpectrumFreq/CI.TOW2/CI.TOW2.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/EventSpectrumFreq/CI.TOW2/CI.TOW2.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/EventSpectrumSpec",
        "AuxiliaryData/Cache/EventSpectrumSpec/CI.CCC",
        "AuxiliaryData/Cache/EventSpectrumSpec/CI.CCC/CI.CCC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/EventSpectrumSpec/CI.CCC/CI.CCC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/EventSpectrumSpec/CI.CCC/CI.CCC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/EventSpectrumSpec/CI.CLC",
        "AuxiliaryData/Cache/EventSpectrumSpec/CI.CLC/CI.CLC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/EventSpectrumSpec/CI.CLC/CI.CLC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/EventSpectrumSpec/CI.CLC/CI.CLC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/EventSpectrumSpec/CI.TOW2",
        "AuxiliaryData/Cache/EventSpectrumSpec/CI.TOW2/CI.TOW2.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/EventSpectrumSpec/CI.TOW2/CI.TOW2.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/EventSpectrumSpec/CI.TOW2/CI.TOW2.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/NoiseSpectrumFreq",
        "AuxiliaryData/Cache/NoiseSpectrumFreq/CI.CCC",
        "AuxiliaryData/Cache/NoiseSpectrumFreq/CI.CCC/CI.CCC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/NoiseSpectrumFreq/CI.CCC/CI.CCC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/NoiseSpectrumFreq/CI.CCC/CI.CCC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/NoiseSpectrumFreq/CI.CLC",
        "AuxiliaryData/Cache/NoiseSpectrumFreq/CI.CLC/CI.CLC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/NoiseSpectrumFreq/CI.CLC/CI.CLC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/NoiseSpectrumFreq/CI.CLC/CI.CLC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/NoiseSpectrumFreq/CI.TOW2",
        "AuxiliaryData/Cache/NoiseSpectrumFreq/CI.TOW2/CI.TOW2.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/NoiseSpectrumFreq/CI.TOW2/CI.TOW2.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/NoiseSpectrumFreq/CI.TOW2/CI.TOW2.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/NoiseSpectrumSpec",
        "AuxiliaryData/Cache/NoiseSpectrumSpec/CI.CCC",
        "AuxiliaryData/Cache/NoiseSpectrumSpec/CI.CCC/CI.CCC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/NoiseSpectrumSpec/CI.CCC/CI.CCC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/NoiseSpectrumSpec/CI.CCC/CI.CCC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/NoiseSpectrumSpec/CI.CLC",
        "AuxiliaryData/Cache/NoiseSpectrumSpec/CI.CLC/CI.CLC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/NoiseSpectrumSpec/CI.CLC/CI.CLC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/NoiseSpectrumSpec/CI.CLC/CI.CLC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/NoiseSpectrumSpec/CI.TOW2",
        "AuxiliaryData/Cache/NoiseSpectrumSpec/CI.TOW2/CI.TOW2.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/NoiseSpectrumSpec/CI.TOW2/CI.TOW2.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/NoiseSpectrumSpec/CI.TOW2/CI.TOW2.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/PreeventNoiseTraceData",
        "AuxiliaryData/Cache/PreeventNoiseTraceData/CI.CCC",
        "AuxiliaryData/Cache/PreeventNoiseTraceData/CI.CCC/CI.CCC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/PreeventNoiseTraceData/CI.CCC/CI.CCC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/PreeventNoiseTraceData/CI.CCC/CI.CCC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/PreeventNoiseTraceData/CI.CLC",
        "AuxiliaryData/Cache/PreeventNoiseTraceData/CI.CLC/CI.CLC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/PreeventNoiseTraceData/CI.CLC/CI.CLC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/PreeventNoiseTraceData/CI.CLC/CI.CLC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/PreeventNoiseTraceData/CI.TOW2",
        "AuxiliaryData/Cache/PreeventNoiseTraceData/CI.TOW2/CI.TOW2.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/PreeventNoiseTraceData/CI.TOW2/CI.TOW2.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/PreeventNoiseTraceData/CI.TOW2/CI.TOW2.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/PreeventNoiseTraceTimes",
        "AuxiliaryData/Cache/PreeventNoiseTraceTimes/CI.CCC",
        "AuxiliaryData/Cache/PreeventNoiseTraceTimes/CI.CCC/CI.CCC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/PreeventNoiseTraceTimes/CI.CCC/CI.CCC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/PreeventNoiseTraceTimes/CI.CCC/CI.CCC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/PreeventNoiseTraceTimes/CI.CLC",
        "AuxiliaryData/Cache/PreeventNoiseTraceTimes/CI.CLC/CI.CLC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/PreeventNoiseTraceTimes/CI.CLC/CI.CLC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/PreeventNoiseTraceTimes/CI.CLC/CI.CLC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/PreeventNoiseTraceTimes/CI.TOW2",
        "AuxiliaryData/Cache/PreeventNoiseTraceTimes/CI.TOW2/CI.TOW2.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/PreeventNoiseTraceTimes/CI.TOW2/CI.TOW2.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/PreeventNoiseTraceTimes/CI.TOW2/CI.TOW2.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/SignalSpectrumFreq",
        "AuxiliaryData/Cache/SignalSpectrumFreq/CI.CCC",
        "AuxiliaryData/Cache/SignalSpectrumFreq/CI.CCC/CI.CCC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/SignalSpectrumFreq/CI.CCC/CI.CCC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/SignalSpectrumFreq/CI.CCC/CI.CCC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/SignalSpectrumFreq/CI.CLC",
        "AuxiliaryData/Cache/SignalSpectrumFreq/CI.CLC/CI.CLC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/SignalSpectrumFreq/CI.CLC/CI.CLC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/SignalSpectrumFreq/CI.CLC/CI.CLC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/SignalSpectrumFreq/CI.TOW2",
        "AuxiliaryData/Cache/SignalSpectrumFreq/CI.TOW2/CI.TOW2.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/SignalSpectrumFreq/CI.TOW2/CI.TOW2.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/SignalSpectrumFreq/CI.TOW2/CI.TOW2.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/SignalSpectrumSpec",
        "AuxiliaryData/Cache/SignalSpectrumSpec/CI.CCC",
        "AuxiliaryData/Cache/SignalSpectrumSpec/CI.CCC/CI.CCC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/SignalSpectrumSpec/CI.CCC/CI.CCC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/SignalSpectrumSpec/CI.CCC/CI.CCC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/SignalSpectrumSpec/CI.CLC",
        "AuxiliaryData/Cache/SignalSpectrumSpec/CI.CLC/CI.CLC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/SignalSpectrumSpec/CI.CLC/CI.CLC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/SignalSpectrumSpec/CI.CLC/CI.CLC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/SignalSpectrumSpec/CI.TOW2",
        "AuxiliaryData/Cache/SignalSpectrumSpec/CI.TOW2/CI.TOW2.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/SignalSpectrumSpec/CI.TOW2/CI.TOW2.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/SignalSpectrumSpec/CI.TOW2/CI.TOW2.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/SmoothEventSpectrumFreq",
        "AuxiliaryData/Cache/SmoothEventSpectrumFreq/CI.CCC",
        "AuxiliaryData/Cache/SmoothEventSpectrumFreq/CI.CCC/CI.CCC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/SmoothEventSpectrumFreq/CI.CCC/CI.CCC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/SmoothEventSpectrumFreq/CI.CCC/CI.CCC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/SmoothEventSpectrumFreq/CI.CLC",
        "AuxiliaryData/Cache/SmoothEventSpectrumFreq/CI.CLC/CI.CLC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/SmoothEventSpectrumFreq/CI.CLC/CI.CLC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/SmoothEventSpectrumFreq/CI.CLC/CI.CLC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/SmoothEventSpectrumFreq/CI.TOW2",
        "AuxiliaryData/Cache/SmoothEventSpectrumFreq/CI.TOW2/CI.TOW2.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/SmoothEventSpectrumFreq/CI.TOW2/CI.TOW2.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/SmoothEventSpectrumFreq/CI.TOW2/CI.TOW2.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/SmoothEventSpectrumSpec",
        "AuxiliaryData/Cache/SmoothEventSpectrumSpec/CI.CCC",
        "AuxiliaryData/Cache/SmoothEventSpectrumSpec/CI.CCC/CI.CCC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/SmoothEventSpectrumSpec/CI.CCC/CI.CCC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/SmoothEventSpectrumSpec/CI.CCC/CI.CCC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/SmoothEventSpectrumSpec/CI.CLC",
        "AuxiliaryData/Cache/SmoothEventSpectrumSpec/CI.CLC/CI.CLC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/SmoothEventSpectrumSpec/CI.CLC/CI.CLC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/SmoothEventSpectrumSpec/CI.CLC/CI.CLC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/SmoothEventSpectrumSpec/CI.TOW2",
        "AuxiliaryData/Cache/SmoothEventSpectrumSpec/CI.TOW2/CI.TOW2.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/SmoothEventSpectrumSpec/CI.TOW2/CI.TOW2.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/SmoothEventSpectrumSpec/CI.TOW2/CI.TOW2.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/SmoothNoiseSpectrumFreq",
        "AuxiliaryData/Cache/SmoothNoiseSpectrumFreq/CI.CCC",
        "AuxiliaryData/Cache/SmoothNoiseSpectrumFreq/CI.CCC/CI.CCC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/SmoothNoiseSpectrumFreq/CI.CCC/CI.CCC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/SmoothNoiseSpectrumFreq/CI.CCC/CI.CCC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/SmoothNoiseSpectrumFreq/CI.CLC",
        "AuxiliaryData/Cache/SmoothNoiseSpectrumFreq/CI.CLC/CI.CLC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/SmoothNoiseSpectrumFreq/CI.CLC/CI.CLC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/SmoothNoiseSpectrumFreq/CI.CLC/CI.CLC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/SmoothNoiseSpectrumFreq/CI.TOW2",
        "AuxiliaryData/Cache/SmoothNoiseSpectrumFreq/CI.TOW2/CI.TOW2.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/SmoothNoiseSpectrumFreq/CI.TOW2/CI.TOW2.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/SmoothNoiseSpectrumFreq/CI.TOW2/CI.TOW2.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/SmoothNoiseSpectrumSpec",
        "AuxiliaryData/Cache/SmoothNoiseSpectrumSpec/CI.CCC",
        "AuxiliaryData/Cache/SmoothNoiseSpectrumSpec/CI.CCC/CI.CCC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/SmoothNoiseSpectrumSpec/CI.CCC/CI.CCC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/SmoothNoiseSpectrumSpec/CI.CCC/CI.CCC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/SmoothNoiseSpectrumSpec/CI.CLC",
        "AuxiliaryData/Cache/SmoothNoiseSpectrumSpec/CI.CLC/CI.CLC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/SmoothNoiseSpectrumSpec/CI.CLC/CI.CLC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/SmoothNoiseSpectrumSpec/CI.CLC/CI.CLC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/SmoothNoiseSpectrumSpec/CI.TOW2",
        "AuxiliaryData/Cache/SmoothNoiseSpectrumSpec/CI.TOW2/CI.TOW2.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/SmoothNoiseSpectrumSpec/CI.TOW2/CI.TOW2.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/SmoothNoiseSpectrumSpec/CI.TOW2/CI.TOW2.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/SmoothSignalSpectrumFreq",
        "AuxiliaryData/Cache/SmoothSignalSpectrumFreq/CI.CCC",
        "AuxiliaryData/Cache/SmoothSignalSpectrumFreq/CI.CCC/CI.CCC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/SmoothSignalSpectrumFreq/CI.CCC/CI.CCC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/SmoothSignalSpectrumFreq/CI.CCC/CI.CCC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/SmoothSignalSpectrumFreq/CI.CLC",
        "AuxiliaryData/Cache/SmoothSignalSpectrumFreq/CI.CLC/CI.CLC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/SmoothSignalSpectrumFreq/CI.CLC/CI.CLC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/SmoothSignalSpectrumFreq/CI.CLC/CI.CLC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/SmoothSignalSpectrumFreq/CI.TOW2",
        "AuxiliaryData/Cache/SmoothSignalSpectrumFreq/CI.TOW2/CI.TOW2.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/SmoothSignalSpectrumFreq/CI.TOW2/CI.TOW2.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/SmoothSignalSpectrumFreq/CI.TOW2/CI.TOW2.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/SmoothSignalSpectrumSpec",
        "AuxiliaryData/Cache/SmoothSignalSpectrumSpec/CI.CCC",
        "AuxiliaryData/Cache/SmoothSignalSpectrumSpec/CI.CCC/CI.CCC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/SmoothSignalSpectrumSpec/CI.CCC/CI.CCC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/SmoothSignalSpectrumSpec/CI.CCC/CI.CCC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/SmoothSignalSpectrumSpec/CI.CLC",
        "AuxiliaryData/Cache/SmoothSignalSpectrumSpec/CI.CLC/CI.CLC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/SmoothSignalSpectrumSpec/CI.CLC/CI.CLC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/SmoothSignalSpectrumSpec/CI.CLC/CI.CLC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/SmoothSignalSpectrumSpec/CI.TOW2",
        "AuxiliaryData/Cache/SmoothSignalSpectrumSpec/CI.TOW2/CI.TOW2.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/SmoothSignalSpectrumSpec/CI.TOW2/CI.TOW2.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/SmoothSignalSpectrumSpec/CI.TOW2/CI.TOW2.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/SnrFreq",
        "AuxiliaryData/Cache/SnrFreq/CI.CCC",
        "AuxiliaryData/Cache/SnrFreq/CI.CCC/CI.CCC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/SnrFreq/CI.CCC/CI.CCC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/SnrFreq/CI.CCC/CI.CCC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/SnrFreq/CI.CLC",
        "AuxiliaryData/Cache/SnrFreq/CI.CLC/CI.CLC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/SnrFreq/CI.CLC/CI.CLC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/SnrFreq/CI.CLC/CI.CLC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/SnrFreq/CI.TOW2",
        "AuxiliaryData/Cache/SnrFreq/CI.TOW2/CI.TOW2.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/SnrFreq/CI.TOW2/CI.TOW2.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/SnrFreq/CI.TOW2/CI.TOW2.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/SnrSnr",
        "AuxiliaryData/Cache/SnrSnr/CI.CCC",
        "AuxiliaryData/Cache/SnrSnr/CI.CCC/CI.CCC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/SnrSnr/CI.CCC/CI.CCC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/SnrSnr/CI.CCC/CI.CCC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/SnrSnr/CI.CLC",
        "AuxiliaryData/Cache/SnrSnr/CI.CLC/CI.CLC.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/SnrSnr/CI.CLC/CI.CLC.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/SnrSnr/CI.CLC/CI.CLC.--.HNZ_ci38457511_default",
        "AuxiliaryData/Cache/SnrSnr/CI.TOW2",
        "AuxiliaryData/Cache/SnrSnr/CI.TOW2/CI.TOW2.--.HN1_ci38457511_default",
        "AuxiliaryData/Cache/SnrSnr/CI.TOW2/CI.TOW2.--.HN2_ci38457511_default",
        "AuxiliaryData/Cache/SnrSnr/CI.TOW2/CI.TOW2.--.HNZ_ci38457511_default",
        "AuxiliaryData/StationMetrics",
        "AuxiliaryData/StationMetrics/CI.CCC",
        "AuxiliaryData/StationMetrics/CI.CCC/CI.CCC.--.HN_ci38457511",
        "AuxiliaryData/StationMetrics/CI.CLC",
        "AuxiliaryData/StationMetrics/CI.CLC/CI.CLC.--.HN_ci38457511",
        "AuxiliaryData/StationMetrics/CI.TOW2",
        "AuxiliaryData/StationMetrics/CI.TOW2/CI.TOW2.--.HN_ci38457511",
        "AuxiliaryData/StreamProcessingParameters",
        "AuxiliaryData/StreamProcessingParameters/CI.CCC",
        "AuxiliaryData/StreamProcessingParameters/CI.CCC/CI.CCC.--.HN_ci38457511_default",
        "AuxiliaryData/StreamProcessingParameters/CI.CCC/CI.CCC.--.HN_ci38457511_unprocessed",
        "AuxiliaryData/StreamProcessingParameters/CI.CLC",
        "AuxiliaryData/StreamProcessingParameters/CI.CLC/CI.CLC.--.HN_ci38457511_default",
        "AuxiliaryData/StreamProcessingParameters/CI.CLC/CI.CLC.--.HN_ci38457511_unprocessed",
        "AuxiliaryData/StreamProcessingParameters/CI.TOW2",
        "AuxiliaryData/StreamProcessingParameters/CI.TOW2/CI.TOW2.--.HN_ci38457511_default",
        "AuxiliaryData/StreamProcessingParameters/CI.TOW2/CI.TOW2.--.HN_ci38457511_unprocessed",
        "AuxiliaryData/StreamSupplementalStats",
        "AuxiliaryData/StreamSupplementalStats/CI.CCC",
        "AuxiliaryData/StreamSupplementalStats/CI.CCC/CI.CCC.--.HN_ci38457511_default",
        "AuxiliaryData/StreamSupplementalStats/CI.CCC/CI.CCC.--.HN_ci38457511_unprocessed",
        "AuxiliaryData/StreamSupplementalStats/CI.CLC",
        "AuxiliaryData/StreamSupplementalStats/CI.CLC/CI.CLC.--.HN_ci38457511_default",
        "AuxiliaryData/StreamSupplementalStats/CI.CLC/CI.CLC.--.HN_ci38457511_unprocessed",
        "AuxiliaryData/StreamSupplementalStats/CI.TOW2",
        "AuxiliaryData/StreamSupplementalStats/CI.TOW2/CI.TOW2.--.HN_ci38457511_default",
        "AuxiliaryData/StreamSupplementalStats/CI.TOW2/CI.TOW2.--.HN_ci38457511_unprocessed",
        "AuxiliaryData/TraceProcessingParameters",
        "AuxiliaryData/TraceProcessingParameters/CI.CCC",
        "AuxiliaryData/TraceProcessingParameters/CI.CCC/CI.CCC.--.HN1_ci38457511_default",
        "AuxiliaryData/TraceProcessingParameters/CI.CCC/CI.CCC.--.HN1_ci38457511_unprocessed",
        "AuxiliaryData/TraceProcessingParameters/CI.CCC/CI.CCC.--.HN2_ci38457511_default",
        "AuxiliaryData/TraceProcessingParameters/CI.CCC/CI.CCC.--.HN2_ci38457511_unprocessed",
        "AuxiliaryData/TraceProcessingParameters/CI.CCC/CI.CCC.--.HNZ_ci38457511_default",
        "AuxiliaryData/TraceProcessingParameters/CI.CCC/CI.CCC.--.HNZ_ci38457511_unprocessed",
        "AuxiliaryData/TraceProcessingParameters/CI.CLC",
        "AuxiliaryData/TraceProcessingParameters/CI.CLC/CI.CLC.--.HN1_ci38457511_default",
        "AuxiliaryData/TraceProcessingParameters/CI.CLC/CI.CLC.--.HN1_ci38457511_unprocessed",
        "AuxiliaryData/TraceProcessingParameters/CI.CLC/CI.CLC.--.HN2_ci38457511_default",
        "AuxiliaryData/TraceProcessingParameters/CI.CLC/CI.CLC.--.HN2_ci38457511_unprocessed",
        "AuxiliaryData/TraceProcessingParameters/CI.CLC/CI.CLC.--.HNZ_ci38457511_default",
        "AuxiliaryData/TraceProcessingParameters/CI.CLC/CI.CLC.--.HNZ_ci38457511_unprocessed",
        "AuxiliaryData/TraceProcessingParameters/CI.TOW2",
        "AuxiliaryData/TraceProcessingParameters/CI.TOW2/CI.TOW2.--.HN1_ci38457511_default",
        "AuxiliaryData/TraceProcessingParameters/CI.TOW2/CI.TOW2.--.HN1_ci38457511_unprocessed",
        "AuxiliaryData/TraceProcessingParameters/CI.TOW2/CI.TOW2.--.HN2_ci38457511_default",
        "AuxiliaryData/TraceProcessingParameters/CI.TOW2/CI.TOW2.--.HN2_ci38457511_unprocessed",
        "AuxiliaryData/TraceProcessingParameters/CI.TOW2/CI.TOW2.--.HNZ_ci38457511_default",
        "AuxiliaryData/TraceProcessingParameters/CI.TOW2/CI.TOW2.--.HNZ_ci38457511_unprocessed",
        "AuxiliaryData/WaveFormMetrics",
        "AuxiliaryData/WaveFormMetrics/CI.CCC",
        "AuxiliaryData/WaveFormMetrics/CI.CCC/CI.CCC.--.HN_ci38457511_default",
        "AuxiliaryData/WaveFormMetrics/CI.CLC",
        "AuxiliaryData/WaveFormMetrics/CI.CLC/CI.CLC.--.HN_ci38457511_default",
        "AuxiliaryData/WaveFormMetrics/CI.TOW2",
        "AuxiliaryData/WaveFormMetrics/CI.TOW2/CI.TOW2.--.HN_ci38457511_default",
        "AuxiliaryData/config",
        "AuxiliaryData/config/config",
        "AuxiliaryData/gmprocess_version",
        "AuxiliaryData/gmprocess_version/version",
        "Provenance",
        "Provenance/CI.CCC.--.HN1_ci38457511_default",
        "Provenance/CI.CCC.--.HN1_ci38457511_unprocessed",
        "Provenance/CI.CCC.--.HN2_ci38457511_default",
        "Provenance/CI.CCC.--.HN2_ci38457511_unprocessed",
        "Provenance/CI.CCC.--.HNZ_ci38457511_default",
        "Provenance/CI.CCC.--.HNZ_ci38457511_unprocessed",
        "Provenance/CI.CLC.--.HN1_ci38457511_default",
        "Provenance/CI.CLC.--.HN1_ci38457511_unprocessed",
        "Provenance/CI.CLC.--.HN2_ci38457511_default",
        "Provenance/CI.CLC.--.HN2_ci38457511_unprocessed",
        "Provenance/CI.CLC.--.HNZ_ci38457511_default",
        "Provenance/CI.CLC.--.HNZ_ci38457511_unprocessed",
        "Provenance/CI.TOW2.--.HN1_ci38457511_default",
        "Provenance/CI.TOW2.--.HN1_ci38457511_unprocessed",
        "Provenance/CI.TOW2.--.HN2_ci38457511_default",
        "Provenance/CI.TOW2.--.HN2_ci38457511_unprocessed",
        "Provenance/CI.TOW2.--.HNZ_ci38457511_default",
        "Provenance/CI.TOW2.--.HNZ_ci38457511_unprocessed",
        "Provenance/default",
        "Provenance/unprocessed",
        "QuakeML",
        "Waveforms",
        "Waveforms/CI.CCC",
        "Waveforms/CI.CCC/CI.CCC.--.HN1__2019-07-06T03:19:37__2019-07-06T03:25:31__ci38457511_unprocessed",
        "Waveforms/CI.CCC/CI.CCC.--.HN1__2019-07-06T03:19:37__2019-07-06T03:21:00__ci38457511_default",
        "Waveforms/CI.CCC/CI.CCC.--.HN2__2019-07-06T03:19:37__2019-07-06T03:25:31__ci38457511_unprocessed",
        "Waveforms/CI.CCC/CI.CCC.--.HN2__2019-07-06T03:19:37__2019-07-06T03:21:00__ci38457511_default",
        "Waveforms/CI.CCC/CI.CCC.--.HNZ__2019-07-06T03:19:37__2019-07-06T03:25:31__ci38457511_unprocessed",
        "Waveforms/CI.CCC/CI.CCC.--.HNZ__2019-07-06T03:19:37__2019-07-06T03:21:00__ci38457511_default",
        "Waveforms/CI.CCC/StationXML",
        "Waveforms/CI.CLC",
        "Waveforms/CI.CLC/CI.CLC.--.HN1__2019-07-06T03:16:08__2019-07-06T03:21:27__ci38457511_unprocessed",
        "Waveforms/CI.CLC/CI.CLC.--.HN1__2019-07-06T03:19:24__2019-07-06T03:20:33__ci38457511_default",
        "Waveforms/CI.CLC/CI.CLC.--.HN2__2019-07-06T03:16:08__2019-07-06T03:21:27__ci38457511_unprocessed",
        "Waveforms/CI.CLC/CI.CLC.--.HN2__2019-07-06T03:19:24__2019-07-06T03:20:33__ci38457511_default",
        "Waveforms/CI.CLC/CI.CLC.--.HNZ__2019-07-06T03:16:08__2019-07-06T03:21:27__ci38457511_unprocessed",
        "Waveforms/CI.CLC/CI.CLC.--.HNZ__2019-07-06T03:19:24__2019-07-06T03:20:33__ci38457511_default",
        "Waveforms/CI.CLC/StationXML",
        "Waveforms/CI.TOW2",
        "Waveforms/CI.TOW2/CI.TOW2.--.HN1__2019-07-06T03:19:31__2019-07-06T03:25:26__ci38457511_unprocessed",
        "Waveforms/CI.TOW2/CI.TOW2.--.HN1__2019-07-06T03:19:31__2019-07-06T03:20:43__ci38457511_default",
        "Waveforms/CI.TOW2/CI.TOW2.--.HN2__2019-07-06T03:19:31__2019-07-06T03:25:26__ci38457511_unprocessed",
        "Waveforms/CI.TOW2/CI.TOW2.--.HN2__2019-07-06T03:19:31__2019-07-06T03:20:43__ci38457511_default",
        "Waveforms/CI.TOW2/CI.TOW2.--.HNZ__2019-07-06T03:19:31__2019-07-06T03:25:26__ci38457511_unprocessed",
        "Waveforms/CI.TOW2/CI.TOW2.--.HNZ__2019-07-06T03:19:31__2019-07-06T03:20:43__ci38457511_default",
        "Waveforms/CI.TOW2/StationXML",
    )

    try:
        cdir = constants.CONFIG_PATH_TEST
        ddir = constants.TEST_DATA_DIR / "demo"

        args = {
            "debug": False,
            "quiet": False,
            "event_id": EVENT_ID,
            "textfile": None,
            "overwrite": False,
            "num_processes": 0,
            "label": None,
            "datadir": ddir,
            "confdir": cdir,
            "resume": None,
        }

        app = GMrecordsApp()
        app.load_subcommands()

        subcommand = "autoprocess"
        step_args = {
            "subcommand": subcommand,
            "func": app.classes[subcommand]["class"],
            "log": None,
            "no_download": True,
            "no_report": True,
            "no_maps": True,
        }
        args.update(step_args)
        app.main(**args)

        ws_filename = ddir / EVENT_ID / constants.WORKSPACE_NAME
        tests_utils.check_workspace(ws_filename, WORKSPACE_ITEMS)

    except Exception as ex:
        raise ex
    finally:
        # Remove workspace and image files
        pattern = [
            "workspace.h5",
            ".png",
            ".csv",
            ".html",
            "_dat.json",
            "_groundmotion_packet.json",
        ]
        for root, _, files in os.walk(ddir):
            for file in files:
                if any(file.endswith(ext) for ext in pattern):
                    os.remove(os.path.join(root, file))
