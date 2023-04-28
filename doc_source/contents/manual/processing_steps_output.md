
## adjust_highpass_corner
```
Adjust high pass corner frequency.

    Options for further refinement of the highpass corner. Currently, this
    includes criteria employed by:

        Dawood, H.M., Rodriguez-Marek, A., Bayless, J., Goulet, C. and
        Thompson, E. (2016). A flatfile for the KiK-net database processed
        using an automated protocol. Earthquake Spectra, 32(2), pp.1281-1302.

    This algorithm begins with an initial corner frequency that was selected
    as configured in the `get_corner_frequencies` step. It then chcks the
    criteria descibed below; if the criteria are not met then the high pass
    corner is increased the multiplicative step factor until the criteria
    are met.

    Args:
        st (StationStream):
            Stream of data.
        step_factor (float):
            Multiplicative factor for incrementing high pass corner.
        maximum_freq (float):
            Limit (maximum) frequency on the trial corner frequencies
            to search across to pass displacement checks.
        max_final_displacement (float):
            Maximum allowable value (in cm) for final displacement.
        max_displacment_ratio (float):
            Maximum allowable ratio of final displacement to max displacment.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: With highpass corner frequency adjusted using Dawood method.
    
```

## check_clipping
```
Apply clicking check.

    Lower thresholds will pass fewer streams but will give less false negatives
    (i.e., streams in which clipping actually occurred but were missed).

    Args:
        st (gmprocess.core.stationstream.StationStream):
           Trace of data.
        event (gmprocess.utils.event.ScalarEvent):
            ScalarEvent object.
        threshold (float):
            Threshold probability.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: With clipping check applied.

    
```

## check_free_field
```
Checks free field status of stream.

    Args:
        st (gmprocess.core.stationstream.StationStream):
            Stream of data.
        reject_non_free_field (bool):
            Should non free-field stations be failed?
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: That has been checked for free field status.
    
```

## check_instrument
```
Test the channels of the station.

    The purpose of the maximum limit is to skip over stations with muliple
    strong motion instruments, which can occur with downhole or structural
    arrays since our code currently is not able to reliably group by location
    within an array.

    The purpose of the minimum and require_two_horiz checks are to ensure the
    channels are required for subsequent intensity measures such as ROTD.

    Args:
        st (gmprocess.core.stationstream.StationStream):
            Stream of data.
        n_max (int):
            Maximum allowed number of streams; default to 3.
        n_min (int):
            Minimum allowed number of streams; default to 1.
        require_two_horiz (bool):
            Require two horizontal components; default to `False`.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: With instrument criteria applied.
    
```

## check_max_amplitude
```
Check the maximum amplitude of the traces.

    Checks that the maximum amplitude of the traces in the stream are within a defined
    range. Only applied to counts/raw data. This is a simple way to screen for clipped
    records, but we now recommend/prefer the `check_clipping` method.

    Args:
        st (gmprocess.core.stationstream.StationStream):
            Stream of data.
        min (float):
            Minimum amplitude for the acceptable range. Default is 5.
        max (float):
            Maximum amplitude for the acceptable range. Default is 2e6.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: That has been checked for maximum amplitude criteria.
    
```

## check_sta_lta
```
Apply STA/LTA ratio criteria.

    Checks that the maximum STA/LTA ratio of the stream's traces is above a threshold.

    Args:
        st (gmprocess.core.stationstream.StationStream):
            Stream of data.
        sta_length (float):
            Length of time window for STA (seconds).
        lta_length (float):
            Length of time window for LTA (seconds).
        threshold (float):
            Required maximum STA/LTA ratio to pass the test.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: That has been checked for sta/lta requirements.
    
```

## check_tail
```
Check for abnormally arge values in the tail of the stream.

    This QA check looks for the presence of abnomally large values in the tail
    velocity and displacement traces. This can occur due to baseline shifts or
    long period noise that has not been properly filtered out that manifest
    as long-period drifts in the velocity and/or displacement traces.

    Note that an additional problem that this check should eliminate is records
    in which the time window has not captured the full duration of shaking.

    Args:
        st (StationStream):
            StationStream object.
        duration (float):
            Duration of tail.
        max_vel_ratio (float):
            Trace is labeled as failed if the max absolute velocity in the tail
            is greater than max_vel_ratio times the max absolute velocity of
            the whole trace.
        max_dis_ratio (float):
            Trace is labeled as failed if the max absolute displacement in the
            tail is greater than max_disp_ratio times the max absolute
            displacement of the whole trace.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: With QA checks applied.
    
```

## check_zero_crossings
```
Requires a minimum zero crossing rate.

    This is intended to screen out instrumental failures or resetting.
    Value determined empirically from observations on the GeoNet network
    by R Lee.

    Args:
        st (StationStream):
            StationStream object.
        min_crossings (float):
            Minimum average number of zero crossings per second for the full
            trace.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: With zero crossing rate criteria applied.
    
```

## compute_snr
```
Compute SNR dictionaries for a stream, looping over all traces.

    Args:
        st (StationStream):
           Trace of data.
        event_magnitude (float):
           Earthquake magnitude.
        bandwidth (float):
           Konno-Omachi smoothing bandwidth parameter.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: With SNR dictionaries added as trace parameters.
    
```

## cut
```
Cut/trim the record.

    This method minimally requires that the windows.signal_end method has been
    run, in which case the record is trimmed to the end of the signal that
    was estimated by that method.

    To trim the beginning of the record, the sec_before_split must be
    specified, which uses the noise/signal split time that was estiamted by the
    windows.signal_split mehtod.

    # Recent changes to reflect major updates to how oq-hazardlib works:
    # https://github.com/gem/oq-engine/issues/7018

    Args:
        st (StationStream):
            Stream of data.
        sec_before_split (float):
            Seconds to trim before split. If None, then the beginning of the
            record will be unchanged.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: With the cut applied.
    
```

## detrend
```
Detrend stream.

    Args:
        st (StationStream):
            Stream of data.
        method (str):
            Method to detrend; valid options include the 'type' options supported by
            obspy.core.trace.Trace.detrend as well as:
                - 'baseline_sixth_order', which is for a baseline correction
                   method that fits a sixth-order polynomial to the
                   displacement time series, and sets the zeroth- and
                   first-order terms to be zero. The second derivative of the
                   fit polynomial is then removed from the acceleration time
                   series.
                - 'pre', for removing the mean of the pre-event noise window.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: With that has been detrended.
    
```

## fit_spectra
```
Fit spectra vaying stress_drop and moment.

    Args:
        st (gmprocess.core.stationstream.StationStream):
            Stream of data.
        event (gmprocess.utils.event.ScalarEvent):
             ScalarEvent object.
        kappa (float):
            Site diminution factor (sec). Typical value for active cruststal
            regions is about 0.03-0.04, and stable continental regions is about
            0.006.
        RP (float):
            Partition of shear-wave energy into horizontal components.
        VHC (float):
            Partition of shear-wave energy into horizontal components
            1 / np.sqrt(2.0).
        FSE (float):
            Free surface effect.
        density (float):
            Density at source (gm/cc).
        shear_vel (float):
            Shear-wave velocity at source (km/s).
        R0 (float):
            Reference distance (km).
        moment_factor (float):
            Multiplicative factor for setting bounds on moment, where the
            moment (from the catalog moment magnitude) is multiplied and
            divided by `moment_factor` to set the bounds for the spectral
            optimization.
        min_stress (float):
            Min stress for fit search (bars).
        max_stress (float):
            Max stress for fit search (bars).
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream with fitted spectra parameters.
    
```

## get_corner_frequencies
```
Select corner frequencies.

    Note that this step only selects the highpass and lowpass corners. The results can
    be modifed by other steps (such as `lowpass_max_frequency`) and then the filters
    are applied with the `lowpass_filter` and `highpass_filter` steps.

    Args:
        st (gmprocess.core.stationstream.StationStream):
            Stream of data.
        event (gmprocess.utils.event.ScalarEvent):
            ScalarEvent object.
        method (str):
            Which method to use; currently allowed "snr" or "constant".
        constant(dict):
            Dictionary of `constant` method config options.
        snr (dict):
            Dictionary of `snr` method config options.
        magnitude (dict):
            Dictionary of `magnitude` method config options.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: With selected corner frequencies added.
    
```

## highpass_filter
```
Apply the highpass filter.

    Args:
        st (StationStream):
            Stream of data.
        frequency_domain (bool):
            If true, use gmprocess frequency domain implementation; if false, use ObsPy
            filters.
        filter_order (int):
            Filter order.
        number_of_passes (int):
            Number of passes.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: With highpass filter applied.
    
```

## lowpass_filter
```
Apply the lowpass filter.

    Args:
        st (StationStream):
            Stream of data.
        frequency_domain (bool):
            If true, use gmprocess frequency domain implementation; if false, use ObsPy
            filters.
        filter_order (int):
            Filter order.
        number_of_passes (int):
            Number of passes.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: Filtered streams.
    
```

## lowpass_max_frequency
```
Cap lowpass corner frequency.

    Options on this include a constant maximum, or as a fraction of the Nyquist.

    Args:
        st (gmprocess.core.stationstream.StationStream):
            Stream of data.
        fn_fac (float):
            Factor to be multiplied by the Nyquist to cap the lowpass filter.
        lp_max (float):
            Maximum lowpass corner frequency (Hz).
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: With lowpass frequency adjustment applied.
    
```

## max_traces
```
Reject a stream if it has more than n_max traces.

    The purpose of this is to skip over stations with muliple strong motion
    instruments, which can occur with downhole or structural arrays since our
    code currently is not able to reliably group by location within an array.

    Args:
        st (gmprocess.core.stationstream.StationStream):
            Stream of data.
        n_max (int):
            Maximum allowed number of streams; default to 3.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: Stream with max number of traces criteria applied.
    
```

## min_sample_rate
```
Require a minimum sample rate.

    Args:
        st (gmprocess.core.stationstream.StationStream):
            Stream of data.
        min_sps (float):
            Minimum samples per second.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: Stream checked for sample rate criteria.
    
```

## NNet_QA
```
Apply the neural network QA algorithm by Bellagamba et al. (2019),

    Assess the quality of a stream by analyzing its two horizontal components
    as described in Bellagamba et al. (2019). Performs three steps:
    1) Compute the quality metrics (see paper for more info)
    2) Preprocess the quality metrics (deskew, standardize and decorrelate)
    3) Evaluate the quality using a neural network-based model
    Two models are available: 'Cant' and 'CantWell'.
    To minimize the number of low quality ground motion included, the natural
    acceptance threshold 0.5 can be raised (up to an extreme value of 0.95).
    Recommended parameters are:
    -   acceptance_threshold = 0.5 or 0.6
    -   model_name = 'CantWell'

    Args:
        st (StationStream):
            The ground motion record to analyze. Should contain at least 2
            orthogonal  horizontal traces.
        acceptance_threshold (float):
            Threshold from which GM records are considered acceptable.
        model_name (string):
            name of the used model ('Cant' or 'CantWell')
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: With QA analysis applied.
    
```

## remove_response
```
Perform the instrument response correction.

    If the response information is not already attached to the stream, then an
    inventory object must be provided. If the instrument is a strong-motion
    accelerometer, then tr.remove_sensitivity() will be used. High-gain seismometers
    will use tr.remove_response() with the defined pre-filter and water level.

    If f3 is Null it will be set to 0.9*fn, if f4 is Null it will be set to fn.

    Args:
        st (StationStream):
            Stream of data.
        pre_filt (bool):
            Apply a bandpass filter in frequency domain to the data before
            deconvolution?
        f1 (float):
            Frequency 1 for pre-filter.
        f2 (float):
            Frequency 2 for pre-filter.
        f3 (float):
            Frequency 3 for pre-filter.
        f4 (float):
            Frequency 4 for pre-filter.
        water_level (float):
            Water level for deconvolution.
        inv (obspy.core.inventory.inventory):
            Obspy inventory object containing response information.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: With instrument response correction applied.
    
```

## resample
```
Resample stream.

    Args:
        st (StationStream):
            Stream of data.
        sampling_rate (float):
            New sampling rate, in Hz.
        method (str):
            Method for interpolation. Currently only supports 'lanczos'.
        a (int):
            Width of the Lanczos window, in number of samples.
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: With resampling applied.
    
```

## ridder_fchp
```
Search for highpass corner using Ridder's method.

    Search such that the criterion that the ratio between the maximum of a third order
    polynomial fit to the displacement time series and the maximum of the displacement
    timeseries is a target % within a tolerance.

    This algorithm searches between a low initial corner frequency a maximum fc.

    Method developed originally by Scott Brandenberg

    Args:
        st (StationStream):
            Stream of data.
        target (float):
            target percentage for ratio between max polynomial value and max
            displacement.
        tol (float):
            tolereance for matching the ratio target
        maxiter (float):
            maximum number of allowed iterations in Ridder's method
        maxfc (float):
            Maximum allowable value of the highpass corner freq.
        int_method (string):
            method used to perform integration between acceleration, velocity, and
            dispacement. Options are "frequency_domain", "time_domain_zero_init" or
            "time_domain_zero_mean"
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: With the highpass corner adjusted using Ridder's method.
    
```

## snr_check
```
Check signal-to-noise ratio.

    Requires noise/signal windowing to have succeeded.

    Args:
        st (StationStream):
           Trace of data.
        mag (float):
            Earthquake magnitude.
        threshold (float):
            Threshold SNR value.
        min_freq (float or str):
            Minimum frequency for threshold to be exeeded. If 'f0', then the
            Brune corner frequency will be used.
        max_freq (float):
            Maximum frequency for threshold to be exeeded.
        bandwidth (float):
            Konno-Omachi smoothing bandwidth parameter.
        f0_options (dict):
            Dictionary of f0 options (see config file).
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        trace: Trace with SNR check.
    
```

## taper
```
Taper streams.

    Args:
        st (StationStream):
            Stream of data.
        type (str):
            Taper type.
        width (float):
            Taper width as percentage of trace length.
        side (str):
            Valid options: "both", "left", "right".
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        StationStream: With the taper applied.
    
```

## trim_multiple_events
```
Trim record windows based on local event catalog and travel times.

    Uses a catalog (list of ScalarEvents) to handle cases where a trace might
    contain signals from multiple events. The catalog should contain events
    down to a low enough magnitude in relation to the events of interest.
    Overall, the algorithm is as follows:

    1) For each earthquake in the catalog, get the P-wave travel time
       and estimated PGA at this station.

    2) Compute the PGA (of the as-recorded horizontal channels).

    3) Select the P-wave arrival times across all events for this record
       that are (a) within the signal window, and (b) the predicted PGA is
       greater than pga_factor times the PGA from step #1.

    4) If any P-wave arrival times match the above criteria, then if any of
       the arrival times fall within in the first pct_window_reject*100%
       of the signal window, then reject the record. Otherwise, trim the
       record such that the end time does not include any of the arrivals
       selected in step #3.

    Args:
        st (StationStream):
            Stream of data.
        event (ScalarEvent):
            ScalarEvent object associated with the StationStream.
        catalog (list):
            List of ScalarEvent objects.
        travel_time_df (DataFrame):
            A pandas DataFrame that contains the travel time information
            (obtained from
             gmprocess.waveform_processing.phase.create_travel_time_dataframe).
            The columns in the DataFrame are the station ids and the indices
            are the earthquake ids.
        pga_factor (float):
            A decimal factor used to determine whether the predicted PGA
            from an event arrival is significant enough that it should be
            considered for removal.
        pct_window_reject (float):
           A decimal from 0.0 to 1.0 used to determine if an arrival should
            be trimmed from the record, or if the entire record should be
            rejected. If the arrival falls within the first
            pct_window_reject * 100% of the signal window, then the entire
            record will be rejected. Otherwise, the record will be trimmed
            appropriately.
        gmpe (str):
            Short name of the GMPE to use. Must be defined in the modules file.
        site_parameters (dict):
            Dictionary of site parameters to input to the GMPE.
        rupture_parameters:
            Dictionary of rupture parameters to input to the GMPE.

    Returns:
        StationStream: Trimmed for multiple events.

    
```
