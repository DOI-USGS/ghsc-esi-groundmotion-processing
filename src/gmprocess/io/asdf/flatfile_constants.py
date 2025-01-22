"""Module for storing some constants that are specific to the workspace."""

from gmprocess.utils import constants

EVENT_TABLE_COLUMNS = [
    "id",
    "time",
    "latitude",
    "longitude",
    "depth",
    "magnitude",
    "magnitude_type",
]

# List of columns in the flatfile, along with their descriptions for the README
FLATFILE_COLUMNS = {
    "EarthquakeId": "Event ID from Comcat",
    "EarthquakeTime": "Earthquake origin time (UTC)",
    "EarthquakeLatitude": "Earthquake latitude (decimal degrees)",
    "EarthquakeLongitude": "Earthquake longitude (decimal degrees)",
    "EarthquakeDepth": "Earthquake depth (km)",
    "EarthquakeMagnitude": "Earthquake magnitude",
    "EarthquakeMagnitudeType": "Earthquake magnitude type",
    "Network": "Network code",
    "DataProvider": "Data source provider",
    "StationCode": "Station code",
    "StationID": "Concatenated network, station, and instrument codes",
    "StationDescription": "Station description",
    "StationLatitude": "Station latitude (decimal degrees)",
    "StationLongitude": "Station longitude (decimal degrees)",
    "StationElevation": "Station elevation (m)",
    "SamplingRate": "Record sampling rate (Hz)",
    "BackAzimuth": "Site-to-source azimuth (decimal degrees)",
    "EpicentralDistance": "Epicentral distance (km)",
    "HypocentralDistance": "Hypocentral distance (km)",
    "RuptureDistance": "Closest distance to the rupture plane (km)",
    "RuptureDistanceVar": "Variance of rupture distance estimate (km^2)",
    "JoynerBooreDistance": "Joyner-Boore distance (km)",
    "JoynerBooreDistanceVar": "Variance of Joyner-Boore distance estimate (km^2)",
    "GC2_rx": (
        "Distance measured perpendicular to the fault strike from the surface"
        " projection of the up-dip edge of the fault plane (km)"
    ),
    "GC2_ry": (
        "Distance measured parallel to the fault strike from the midpoint of "
        "the surface projection of the fault plane (km)"
    ),
    "GC2_ry0": (
        "Horizontal distance off the end of the rupture measured parallel to "
        "strike (km)"
    ),
    "GC2_U": (
        "Strike-normal (U) coordinate, defined by Spudich and Chiou (2015; "
        "https://doi.org/10.3133/ofr20151028) (km)"
    ),
    "GC2_T": (
        "Strike-parallel (T) coordinate, defined by Spudich and Chiou "
        "(2015; https://doi.org/10.3133/ofr20151028) (km)"
    ),
    "Lowpass": "Channel lowpass frequency (Hz)",
    "Highpass": "Channel highpass frequency (Hz)",
    "H1Lowpass": "H1 channel lowpass frequency (Hz)",
    "H1Highpass": "H1 channel highpass frequency (Hz)",
    "H2Lowpass": "H2 channel lowpass frequency (Hz)",
    "H2Highpass": "H2 channel highpass frequency (Hz)",
    "ZLowpass": "Vertical channel lowpass frequency (Hz)",
    "ZHighpass": "Vertical channel highpass frequency (Hz)",
    "SourceFile": "Source file",
}

FLATFILE_IMT_COLUMNS = {
    "PGA": f"Peak ground acceleration ({constants.UNITS['pga']})",
    "PGV": f"Peak ground velocity ({constants.UNITS['pgv']})",
    "SA(X)": f"Spectral acceleration ({constants.UNITS['sa']}) at X seconds",
    "PSA(X)": f"Pseudo-spectral acceleration ({constants.UNITS['psa']}) at X seconds",
    "SV(X)": f"Spectral velocity ({constants.UNITS['sv']}) at X seconds",
    "PSV(X)": f"Pseudo-spectral velocity ({constants.UNITS['psv']}) at X seconds",
    "SD(X)": f"Spectral displacmeent ({constants.UNITS['sd']}) at X seconds",
    "FAS(X)": (
        f"Fourier amplitude spectrum value ({constants.UNITS['fas']}) at X seconds"
    ),
    "DURATIONp-q": (
        f"p-q percent significant duration ({constants.UNITS['duration']})"
    ),
    "SORTEDDURATION": (f"Sorted significant duration ({constants.UNITS['duration']})"),
    "ARIAS": f"Arias intensity ({constants.UNITS['arias']})",
    "CAV": f"Cumulative Absolute Velocity ({constants.UNITS['cav']})",
}

# List of columns in the fit_spectra_parameters file, along README descriptions
FIT_SPECTRA_COLUMNS = {
    "EarthquakeId": "Event ID from Comcat",
    "EarthquakeTime": "Earthquake origin time (UTC)",
    "EarthquakeLatitude": "Earthquake latitude (decimal degrees)",
    "EarthquakeLongitude": "Earthquake longitude (decimal degrees)",
    "EarthquakeDepth": "Earthquake depth (km)",
    "EarthquakeMagnitude": "Earthquake magnitude",
    "EarthquakeMagnitudeType": "Earthquake magnitude type",
    "TraceID": "NET.STA.LOC.CHA",
    "StationLatitude": "Station latitude (decimal degrees)",
    "StationLongitude": "Station longitude (decimal degrees)",
    "StationElevation": "Station elevation (m)",
    "fmin": "Record highpass filter frequency (Hz)",
    "fmax": "Record lowpass filter frequency (Hz)",
    "epi_dist": "Epicentral distance (km)",
    "f0": "Brune corner frequency (Hz)",
    "kappa": "Site diminution factor (sec)",
    "magnitude": "Magnitude from optimized moment",
    "minimize_message": "Output message from scipy.optimize.minimize",
    "minimize_success": "Boolean flag indicating if the optimizer exited successfully",
    "moment": "Moment fit (dyne-cm)",
    "moment_lnsd": "Natural log standard deviation of the moment fit",
    "stress_drop": "Stress drop fit (bars)",
    "stress_drop_lnsd": "Natural log standard deviation of the stress drop fit",
    "R2": ("Coefficient of determination between fitted and observed spectra"),
    "mean_squared_error": ("Mean squared error between fitted and observed spectra"),
}

# List of columns in the fit_spectra_parameters file, along README descriptions
SNR_COLUMNS = {
    "EarthquakeId": "Event ID from Comcat",
    "EarthquakeTime": "Earthquake origin time (UTC)",
    "EarthquakeLatitude": "Earthquake latitude (decimal degrees)",
    "EarthquakeLongitude": "Earthquake longitude (decimal degrees)",
    "EarthquakeDepth": "Earthquake depth (km)",
    "EarthquakeMagnitude": "Earthquake magnitude",
    "EarthquakeMagnitudeType": "Earthquake magnitude type",
    "TraceID": "NET.STA.LOC.CHA",
    "StationLatitude": "Station latitude (decimal degrees)",
    "StationLongitude": "Station longitude (decimal degrees)",
    "StationElevation": "Station elevation (m)",
}

SNR_FREQ_COLUMNS = {"SNR(X)": "Signal-to-noise ratio at frequency X."}
