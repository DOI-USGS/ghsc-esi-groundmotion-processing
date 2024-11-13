---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: '0.8'
    jupytext_version: '1.4.1'
kernelspec:
  display_name: Python 3
  language: python
  name: python3
mystnb:
  execution_timeout: 300
---
# Scripting

You can write Python scripts that call the `GMrecordsApp` application to create high-level workflows.
In the example below we create a Python script to run several subcommands to download and process ground motions recorded close to the epicenter of a magnitude 4.5 earthquake, and then export the results to CSV files and generate a report summarizing the results.
The configuration and parameter files are in the `docs/contents/tutorials` directory.

In this tutorial, the commands are written to be executed in [Jupyter Notebooks](https://jupyter.org/). 
Within a Jupyter Notebook, commands can be redirected to the terminal with the `!` symbol and we make ue of this functionality here.

## Local `gmprocess` configuration

In this example we specify parameters in the project configuration to produce a small dataset.
We use only the FDSN fetcher and limit the station distance to 0.1 degrees.
The configuration files are in the `conf/scripting` directory.

First, we list the available projects in the current directory.

```{code-cell} ipython3
!gmrecords projects --list
```

The `PROJECTS_PATH` shows the location of the projects configuration file where the information for the projects is stored.
Second, we use the `projects` subcommand to select the project configuration `scripting-tutorial`.

```{code-cell} ipython3
!gmrecords projects --switch scripting-tutorial
```

Third, we create the directory to hold the data.

:::{note}
We include the directory with the processing parameters for the project in the source code.
:::

At this point we have an empty `data/scripting` directory.
The `conf/scripting` directory has two files: `fetchers/yml` and `user.yml`.
These configuration files hold parameters that override default values provided with the source code.
See [Configuration File](../manual/config_file) for more information.

## Download Data

In this example we will consider ground motions recorded for a [magnitude 4.5 earthquake](https://earthquake.usgs.gov/earthquakes/eventpage/nc73291880/executive) east of San Francisco, California.
We have cached a snippet of the results of running `gmrecords download --eventid nc73291880` in the `tests/data/tutorials` directory.
Consequently, we simply copy the data from `tests/data/tutorials/nc73291880` to `data/scripting/nc73291880`.

```{code-cell} ipython3
!mkdir -p data/scripting/.
!cp -r ../../../tests/data/tutorials/nc73291880 data/scripting/.
```


### List Data

We now have earthquake rupture information and raw waveforms in the `data/scripting` directory.

```{code-cell} ipython3
!tree data/scripting
```

## Python Script

First we need to import the GMrecordsApp application and initial it

```{code-cell} ipython3
from gmprocess.apps.gmrecords import GMrecordsApp

app = GMrecordsApp()
app.load_subcommands()
```

Now, we need to create a dictionary with the arguments common to all subcommands.
We must include arguments that normally are given default values by the command line argument parser.

```{code-cell} ipython3
args = {
    'debug': False,
    'quiet': False,
    'event_id': "nc73291880",
    'textfile': None,
    'overwrite': False,
    'num_processes': 0,
    'label': None,
    'datadir': None,
    'confdir': None,
    'textfile': None,
    'resume': None,
}
```

And let's make a convenience function to make calling the individual subcommands (i.e., "steps") easier

```{code-cell} ipython3
def call_gmprocess_subcommand(subcommand):
    step_args = {
        'subcommand': subcommand,
        'func': app.classes[subcommand]['class'],
        'log': None,
    }
    args.update(step_args)
    app.main(**args)
```

Now we can easily call each subcommand

```{code-cell} ipython3
:tags: [hide-output]
call_gmprocess_subcommand("assemble")
```

```{code-cell} ipython3
:tags: [hide-output]
call_gmprocess_subcommand("process_waveforms")
```

```{code-cell} ipython3
:tags: [hide-output]
call_gmprocess_subcommand("compute_station_metrics")
```

```{code-cell} ipython3
:tags: [hide-output]
call_gmprocess_subcommand("compute_waveform_metrics")
```

```{code-cell} ipython3
:tags: [hide-output]
call_gmprocess_subcommand("export_metric_tables")
```

```{code-cell} ipython3
:tags: [hide-output]
call_gmprocess_subcommand("generate_station_maps")
```

This will produce CSV files with the waveform metrics in the `data/scripting` directory.

```{code-cell} ipython3
!ls -1 data/scripting/*.csv
```

The station map will be in the `data/scripting/nc73291880` directory.

```{code-cell} ipython3
!ls -1 data/scripting/nc73291880/*.html
```
