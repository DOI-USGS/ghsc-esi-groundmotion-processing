# The gmrecords Program

```{seealso}
Be sure to review the discussion of how the `gmrecords` command line interface makes use of "projects" in the {ref}`Initial Setup` section.
```

You can use the `gmrecords` program to download, process, and generate products for ground-motion records from a given set of earthquakes.
Each processing step is a subcommand and you can run only one subcommand at a time.
You can use [Python scripting](scripting) to chain together multiple subcommands.

Use the `-h` command line argument to output the list of subcommands and their descriptions:

:::{command-output} gmrecords -h
:::

Note that some of the subcommands with longer names have short aliases to make the command line calls more concise.
Use the syntax `gmrecords SUBCOMMAND -h` to show the help information for a given subcommand.

## General subcommands

### `config`

:::{command-output} gmrecords config -h
:::

### `clean`

:::{command-output} gmrecords clean -h
:::

### `init`

Create a configuration file for projects in the current directory.

:::{command-output} gmrecords init -h
:::


### `projects`

Manage local directory or system-level projects.
Use this subcommand to switch among projects and add, delete, list, and rename projects.

:::{command-output} gmrecords projects -h
:::

## Data gathering subcommands

### `download`

The `download` subcommand will fetch data for a given set of earthquakes from a variety of data centers.
The data includes the earthquake rupture information (for example, magnitude, location, origin time) and the raw waveforms.

The easiest way to get data for events is by specifying USGS ComCat event IDs.
These event IDs can be found by searching for events on the USGS [Search Earthquake Catalog](https://earthquake.usgs.gov/earthquakes/search/) page.
With `gmrecords` you can specify a single event ID or a list of event IDs in a text file.
Also, you can run customized searches of the earthquake catalog in Python using [libcomcat](https://code.usgs.gov/ghsc/esi/libcomcat-python), [ObsPy](https://github.com/obspy/obspy/wiki/), or webservices directly in your code.

A subdirectory for each event will be created in the data directory of the project with the name of the directory set to the event ID.
Within each subdirectory, the event information will be placed in `event.json` and the raw waveforms in a `raw` subdirectory.
If STREC is enabled to associated events with tectonic regimes, the information will be placed in `strec.json`.

:::{command-output} gmrecords download -h
:::

### `assemble`

The assemble command reads the files in each event subdirectory and creates a corresponding ASDF file `workspace.h5` with the event information and raw waveforms.
All subsequent commands only access the ASDF file.

:::{command-output} gmrecords assemble -h
:::

### `import`

:::{command-output} gmrecords import -h
:::

## Processing subcommands


### `processing_steps`

Print a summary of the currently available processing steps.

:::{command-output} gmrecords processing_steps -h
:::


### `process_waveforms`

Perform processing steps on the raw waveforms, such as baseline correction, bandpass filtering, and trimming.

:::{command-output} gmrecords process_waveforms -h
:::

### `compute_station_metrics`

Compute station metrics, such as rupture distance, and back azimuth to rupture.

:::{command-output} gmrecords compute_station_metrics -h
:::

### `compute_waveform_metrics`

Compute waveform metrics, such as PGA, PGV, pseudospectral acceleration, and Fourier amplitude spectra.

:::{command-output} gmrecords compute_waveform_metrics -h
:::

### `autoshakemap`

An alias for downloading and assembling data, processing waveforms, computing station metrics, computing waveform metrics, and exporting files for ShakeMap.

:::{command-output} gmrecords autoshakemap -h
:::

### `autoprocess`

An alias for downloading and assembling data, processing waveforms, computing station metrics, computing waveform metrics, and generating a report and station map.

:::{command-output} gmrecords autoprocess -h
:::

## Export subcommands

### `export_cosmos`

:::{command-output} gmrecords export_cosmos -h
:::

### `export_failure_tables`

:::{command-output} gmrecords export_failure_tables -h
:::

### `export_gmpacket`

:::{command-output} gmrecords export_gmpacket -h
:::

### `export_metric_tables`

:::{command-output} gmrecords export_metric_tables -h
:::


### `export_provenance_tables`

:::{command-output} gmrecords export_provenance_tables -h
:::


## Diagnostic subcommands

## `generate_regression_plot`

:::{important}
You must run the `export_metric_tables` subcommand before running the `generate_regression_plot` subcommand.
:::

:::{command-output} gmrecords generate_regression_plot -h
:::

## `generate_report`

:::{command-output} gmrecords generate_report -h
:::

## `generate_station_maps`

:::{command-output} gmrecords generate_station_maps -h
:::

