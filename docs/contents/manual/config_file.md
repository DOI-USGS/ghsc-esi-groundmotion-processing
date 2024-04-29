# Configuration File


## Overview

The config file is the primary means by which users can adjust and customize *gmprocess*. 
In this section, we give a quick high-level overview of the config file to illustrate how it works, and subsequent sections go into more detail.
Modifying the config can be somewhat confusing for new users, but bear in mind that if you just want the default config options, you do not have to make any changes to the config file.

The [default config file](https://code.usgs.gov/ghsc/esi/groundmotion-processing/blob/main/src/gmprocess/data/config_production.yml) in the source code includes comments to help explain the values and their units.
This is a useful reference as an overview of the config options. 

When a project is created, it has an associated "config directory." 
The project creation process will create a single file: 

```
conf/
└── user.yml
```

Initially, this file will simply contain your name and email (which you are prompted to provide when creating the project) like this
```yaml
user:
    name: George M. Process
    email: gmprocess@usgs.gov
```

This information is important to put in the data provenance so that anyone you share the data with will have a record of who created it. 

Any `*.yml` files in this directory will be merged with the default config that is in  source code repository. 
The reason for this system is that 
(1) we don't want to overwrite your customized config when the code is updated, and 
(2) by merging your project config into the default config, we avoid breaking functionality that relies on config updates.
(3) specifying all config options can result in a long file, and it can be convenient to break it up into smaller files.

Note that the name of the config files doesn't matter. 
You can put this in the `user.yml`  file or into another file, whatever is most convenient for you. 
For example, it might be convenient to organize the config files by the top level sections:

```
conf/
├── user.yml
├── fetchers.yml
├── windows.yml
...
└── processing.yml
```

A very simple and common change to the config file is to turn specific data fetcheres on or off.
By default, all the fetchers are turned on, but if you know that you are not interested in data from Japan for a specific project, you can turn it off by settign the "enabled" value to "False:
```yaml
fetchers:
    KNETFetcher:
        # Enable this fetcher?
        enabled: True
```

Additionally, if you know that you will be using the KNETFetcher, you will want to enable it and fill in your username and password:
```yaml
fetchers:
    KNETFetcher:
        # Enable this fetcher?
        enabled: True
        user: gmprocess
        password: n0tarea1pa$$w0rd
```


## The "processing" section

The `processing` section behaves somewhat differently than other sections because some steps may need to be repeated. 
The most common example is of this is the `detrend` step, which often has to happen multiple times. 
Here is an example of the processing section that specifies the processing steps but does not specify any of the function arguments except for the `detrend` step:

```yaml
processing:
    - check_free_field:
    - check_instrument:
    - min_sample_rate:
    - check_clipping:
    - detrend:
        detrending_method: linear
    - detrend:
        detrending_method: demean
    - remove_response:
    - detrend:
        detrending_method: linear
    - detrend:
        detrending_method: demean
    - compute_snr:
    - snr_check:
    - get_corner_frequencies:
    - lowpass_max_frequency:
    - cut:
    - taper:
    - highpass_filter:
    - lowpass_filter:
    - detrend:
        detrending_method: pre
    - detrend:
        detrending_method: baseline_sixth_order
    - fit_spectra:
```

The more complex structure in this section is necessary so that you can not only modify the steps that are used, but also control their order. 
Thus, in this section, you turn off a step by deleting it's entry.

To see the available arguments for each step and their default values, you can look up the function in the `gmprocess/waveform_processing` directory 
([here](https://code.usgs.gov/ghsc/esi/groundmotion-processing/-/tree/main/src/gmprocess/waveform_processing)
is the link to it). 

```{Hint}
For those that are familiar with python, each available processing step is marked with the `@processing_step` decorator. 
This makes it easy to find the processing step functions in the source code.
```

One challenge for new users can be identifying the available options for the processing steps. 
For example, let's say you want to change the width for the taper step.
One option is to look in the entry for the `taper` step in the 
[Processing Steps](https://ghsc.code-pages.usgs.gov/esi/groundmotion-processing/contents/manual/processing.html#taper)
section of the manual.
Here, you can see the argument defaults and that the "taper" step has the following arguments:
```
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
```
Note that the `st` and `config` arguments are handled internally by the processing code, and so they are not specified in the config file.
So if you want to change the width, you would modify the entry within "processing" section of the config file like this:

```yaml
    - taper:
        width: 0.1
```

Many sections of the config file are not of interest most of the time, such as the details of the `pickers` section. 
However, the `p_arrival_shift` value is very useful if you are collecting data in a region where the travel time picks are often later than the actual p-wave arrival, causing some of the shaking to be placed in the "noise" window, which in turn causes the record to fail the signal-to-noise ratio test.

Please post any questions or issues that you have regarding the config to the GitLab
[issues](https://code.usgs.gov/ghsc/esi/groundmotion-processing/-/issues) page. 


## The "fetchers" section

The `download` subcommand will look for data from providers configured in the `fetchers` section of the config file.
Three of the subsections correspond to different data retrieval methods, such as the International Federation of Digital Seismograph Networks ([FDSN](https://www.fdsn.org/)). 
The options are:
  1. `FDSNFetcher` for getting data from FDSN services,
  2. `CESMDFetcher` for getting data from the Center for Engineering Strong Motion Data ([CESMD](https://www.strongmotioncenter.org/aboutcesmd.html)), and
  3. `KNETFetcher` for getting data from the [K-NET and KiK-net](https://www.kyoshin.bosai.go.jp/kyoshin/docs/overview_kyoshin_index_en.html) strong-motion seismograph networks in Japan. 

There is also a section that allows search parameters to be computed based on the magnitude and location of the earthquake called `search_parameters`.

Note that each section can be enabled/disabled with the `enabled` key.
Thus, if you know that you don't need data from FDSN services, this part of the config would look like

```yaml
fetchers:
    FDSNFetcher:
        enabled: False
```

### search_parameters

In this section you can configure updates to the search radius and duration of the waveform queries that are based on the magnitude and location of the earthquake.
If this section is enabled, the corresponding static search parameters that are specified in the data fetchers sections will be overwritten by the values computed as configured in this section.

The following is an example of how this section can be configued and includes comments to explain the parameters:

```yaml
    search_parameters:
        enabled: True
        duration:
            # Duration is computed as c0 + c1 * magnitude, in minutes.
            c0: 0.0
            c1: 0.5
        distance:
            # The search radius uses a ground motion model, as specified in the 
            # 'gmm_selection' section. If STREC is enabled, it will select the model
            # based on the tectonic environment of the epicenter and otherwise use the
            # StableShallow GMM.
            # The distance will be the the distance at which the threshold PGA (in g) is
            # exceeded based on the GMM.
            pga: 0.01
            # The maximum distance (in km) that can be returned.
            max_distance: 800.0
            # NOTE: the GMM is evaluated with a number of simplifications, including 
            # Ztor=0 and dip=90 deg such that the 'distance' is both Rrup and Rjb. See 
            # the dynamic_searc_parameters.py module for further details. 
```


### FDSNFetcher

The FDSNFetcher section is organized to mimic obspy's [mass_downloader](https://docs.obspy.org/packages/autogen/obspy.clients.fdsn.mass_downloader.html), which is what gmprocess uses to interact with FDSN web services. 
Thus, there are three main subsections:
  - `domain` - this specifies the search extent and be either `circular` or `rectangular`, as determined by the `type` key. 
    There are additional subsections for options specific to each of these types.
  - `restrictions` - this section corresponds to arguments to obspy's [Restrictions](https://docs.obspy.org/packages/autogen/obspy.clients.fdsn.mass_downloader.restrictions.Restrictions.html) class.
    The exception is that here you can set the `time_before` and `time_after` keys (relative to the earthquake origin time), which will be translated into the `Restrictions` arguments of `starttime` and `endtime`. 
  - `providers` - This section is `None` by default and in this case it will use obspy's list of providers given as `URL_MAPPINGS` in the [FDSN header](https://github.com/obspy/obspy/blob/master/obspy/clients/fdsn/header.py) module. If it is not `None` then it must be a list of dictionaries and more details are given below.

If you only want to use one provider, you can specify one of the keys in `URL_MAPPINGS` as an empty dictionary in the `providers` list:

```yaml
        providers:
            - IRIS: 
```

If you want to use a provider that is not available in the `URL_MAPPINGS` dictionary, then you can specify it like this
```yaml
        providers:
            - IS: 
                url: https://seis.gsi.gov.il/
``` 

### CESMDFetcher

In order to use the `CESMDFetcher` you have to provide an email address that is registered at <www.strongmotioncenter.org>. 
The other options are explained here:

```yaml
    CESMDFetcher:
        # Enable this fetcher?
        enabled: True
        # CESMD requires an email, register at https://strongmotioncenter.org/cgi-bin/CESMD/register.pl
        email: EMAIL
        # One of 'raw' or 'processed'.
        process_type: raw
        # One of "Array", "Ground", "Building", "Bridge", "Dam", "Tunnel", "Wharf", "Other"
        station_type: Ground
        # Distance search radius (km)
        eq_radius: 10.0
        # Time search threshold (sec)
        eq_dt: 10.0
        # Station search radius (km)
        station_radius: 100.0
```

### KNETFetcher

The `KNETFetcher` options are explained here:

```yaml
    KNETFetcher:
        # Enable this fetcher?
        enabled: True
        # NIED requires a username and a password: https://hinetwww11.bosai.go.jp/nied/registration/
        user: USERNAME
        password: PASSWORD
        # Distance search radius (km)
        radius: 100.0
        # Time search threshold (sec)
        dt: 60.0
        # Depth search threshold (km)
        ddepth: 30.0
        # Magnitude search threshold (km)
        dmag: 0.3
        # Restrict the number of processed stations by
        # using magnitude to set maximum station distance
        restrict_stations: false
```

## The "read" section

This section contains some miscellaneous options for data readers. 
A particularly important option is `use_streamcollection`, which is `True` by default. 
The `StreamCollection` class in gmprocess groups channels from the same instrument together and tries to enforce a bunch of useful requirements.
However, these are not desirable for all projects. By setting this to `False`, each channel will be analyzed independently.
This is useful for structural arrays that may have complicated configurations, but comes at the cost of not allowing the computation of some waveform metric types (such as RotDxx, which requires two orthogonal horizontal components that are aligned in time).

## The "windows" section

This section defines how the signal and noise windows are estimated and some relevant QA checks.
The beginning of the signal window is based on an estimated P-wave arrival time, and the relevant options are set in the "pickers" section of the config file. 
The end of the signal window is defined in the `signal_end` subsection here, and the primary choice is set with the `method` key:
   - `velocity`: Set the end of the signal can be set using a phase velocity; this option makes use of the keys `vmin` and `floor`.
   - `model`: Set the end of the signal window using a shaking duration model; this options makes use of the keys `model` and `epsilon`.
   - `magnitude`: Use the magnitude-based signal end as defined by CISN, which is `magnitude/2` (units of minutes).
   - `none`: Use the full available record; this is useful if the records have already been trimmed to a reasonable level and you do not wish to further reduce trace duration.

The `no_noise` option allows processing to run for older data for which no pre-event noise is available.
Essentially it sets the "split time" to be the start time of the record, which would normally fail because it is estiamted as the p-wave arrival time. 


## The "check_stream" section

This section currently only has one key: `any_trace_failures`. 
This controls whether a stream will be marked as failed if ANY of the constituent traces fail a QA check.
If `False` then streams will continue to be processed if some but not all of the traces have failed.
The default is `True`. 

## The "colocated" section

This section includes options for handling colocated instruments. 
More details are given in the default config file:
```yaml
colocated:
    # Enable the colocation algorithm?
    enabled: True
    # This section is for handling colocated instruments that have otherwise
    # passed tests. For reference:
    #
    #    B?? = Broad band
    #    H?? = High broad band
    #    ?N? = Accelerometer
    #    ?H? = High gain seismometer
    #
    # Note: for now, lets prefer accelerometers, but once we have a reliable
    # clipping detection algorithm, it probably makes sense to change the
    # preference to high gain seismometers.

    preference: ["HN?", "BN?", "HH?", "BH?"]

    # Optionally, provide a difference preference order for "large distances", for which
    # the distance threshold can be specified as a function of magnitude. The distance
    # threshold is computed as:
    #     dist_thresh = dist[0]
    #     for m, d in zip(mag, dist):
    #         if eqmag > m:
    #             dist_thresh = d
    large_dist:
        # Enable separate channel preferences at large distances?
        enabled: True

        preference: [HH?, BH?, HN?, BN?]
        mag: [3, 4, 5, 6, 7]
        dist: [20, 50,100, 300, 600]
```

## The "duplicate" section

This section is for handling duplicate data when creating a StreamCollection. 
This includes a spatial tolerance for classifying stations as colocated (`max_dist_tolerance`), as well as options for which data to prefer in the case that data is duplicated (e.g., available from multiple sources in different formats).

## The "build_report" section

This is for building a report, with a one-page summary of the data in each StationStream per page. 
It will write out the latex file, and then look for the `pdflatex` command and attempt to build the pdf. 

## The "metrics" section 

This section is for setting options for the waveform metrics. 
The options are further described in this example:
```yaml
metrics:
  # Specify output IMs (intensity metric)
  # Each IM is defined by an IMC (IM component) and a IMT (IM type)
  # Supported IMCs: channels, arithmetric_mean, geometric_mean, quadratic_mean, rotd
  # Supported IMT: pga, pgv, sa, duration, sorted_duration, arias, fas, cav

  # The 'components_and_types' section has key-value pairs in which the key is the
  # metric component and the value is a list of metric types for that component.
  # Do *not* delete a key to remove a component, it will be replaced with the default.
  # To remove a component, set it's types as an empty list.
  components_and_types: 
    channels: [pga, pgv, sa, duration, cav]
    rotd: [pga, pgv, sa]
    geometric_mean: [duration]
    quadratic_mean: [fas]

  component_parameters:
    rotd:
       percentiles: [50.0]

  type_parameters:
    # Additional parameters required for SA
    sa:
        # damping used to calculate the spectral response; if this list includes more than
        # one value, all periods will be computed for each damping level.
        damping: [0.05]
        # periods for which the spectral response is calculated
        periods: [0.01, 0.02, 0.03, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 7.5, 10.0]

    # Additional parameters required for FAS
    fas:
        smoothing_method: konno_ohmachi
        smoothing_parameter: 20.0
        allow_nans: True
        frequencies:
            # Parameters defining an array of frequencies.
            # syntax is the same as that used for numpy linspace and logspace
            # start (first value), stop (last value), num (number of values)
            start: 0.001
            stop: 100.0
            num: 401

    # Additional parameters required for duration
    duration:
        intervals: [5-75, 5-95]
```

## The "gmm_selection" section

This section is ground motion model selection given the tectonic region. 
Model abbreviaitons are defined in modules.yml

```yaml
gmm_selection:
    ActiveShallow: Bea14
    ActiveDeep: Ask14
    VolcanicShallow: Atk10
    SubductionIntraslab: Pea20slab
    SubductionInterface: Pea20inter
    SubductionCrustal: Ask14
    StableShallow: AB06
```

## The "integration" section 

Options for how integration is performed. 

```yaml
integration:
    # Frequency or time domain integration?
    frequency: True
    # Assumption for the first value returned in the resulting trace.
    initial: 0.0
    # Remove the mean of the data prior to integration.
    demean: False
    # Taper the data prior to integration.
    taper: False
    taper_width: 0.05
    taper_type: hann
    taper_side: both
```

## The "differentiation" section 

Should differentiation be performed in the time or frequency domain?

```yaml
differentiation:
    # Frequency or time domain differentation?
    frequency: True
```

## The "pickers" section 

This section is for options that determine how the P-wave arrival time is estimated.
We do not recommend modifying this section unless you are experiencing problems with the start time of the signal window.
Please see the default config file for additional details.

% Indices and tables

% ==================

% * :ref:`genindex`

% * :ref:`modindex`

% * :ref:`search`

## The "error_notification" section 

This section will allow for automated exception emails to be sent to a specified list of users. This is most 
likely useful for situations where gmrecords is set to run automatically on a server. When using this configuration,
any un-handled exceptions generated at any level in gmprocess modules will cause emails to be sent to the configured list
of users.

```
mail_host: smtp.generic.org # contact your IT department for details
  subject: "Error in gmprocess" # the subject line for all error emails
  from_address: gmprocess@generic.org # the reply address for the emails
  to_addresses: # list of user addresses to which exception emails should be sent
    - user1@generic.org
    - user2@generic.org
```
