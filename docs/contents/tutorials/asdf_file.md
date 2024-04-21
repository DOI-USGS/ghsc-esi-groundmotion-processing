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
---
# Working with the gmprocess ASDF file

For browsing information in the 
[HDF5](https://www.hdfgroup.org/solutions/hdf5/)/[ASDF](https://asdf-definition.readthedocs.io/en/latest/)
files output by gmprocess, the overview of the organizational structure in the 
[Workspace section of the manual](../manual/workspace)
should be a useful reference. 

Note that the `StreamWorkspace` object is essentially a gmprocess wrapper around the ASDF structure, and that ASDF is a specific HDF5 format developed for seismological data.
As such, it is possible to work with the ASDF file using the `StreamWorkspace` functions, the pyasdf library, or the h5py library.

```{note} 
We recommend that users who are new to python and/or gmprocess should only use the `StreamWorkspace` interface, which handles a lot of the more confusing bookkeeping for accessing and arranging data from the various sections of the ASDF file (e.g., `Waveforms`, `AuxiliaryData`, and `Provenance`). 
Only more advanced users should attempt to use the pyasdf and h5py interfaces.
```

## The StreamWorkspace interface

First, some imports

```{code-cell} ipython3
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.utils.constants import DATA_DIR
```

And now we open an example ASDF file

```{code-cell} ipython3
# Path to example data
data_path = DATA_DIR / 'demo' / 'nc72282711' / 'workspace.h5'
workspace = StreamWorkspace.open(data_path)
```

Now, we will check to see what labels are present. 
There is typically the "unprocessed" label and one for the processed waveforms. 
The processed waveform label is "default" unless the user has set the label for the processed waveforms.

```{code-cell} ipython3
labels = workspace.get_labels()
print(labels)
```

It is generally possible to have multiple events in an ASDF file, but gmprocess follows a convention of having one event per ASDF file. 

```{code-cell} ipython3
eventids = workspace.get_event_ids()
print(eventids)
```

If you want a StreamCollection object (see [here](../manual/data_structures) for more info), the `get_streams` function constructs it from the workspace file

```{code-cell} ipython3
sc = workspace.get_streams('nc72282711', stations=['CE.68150'], labels=['default'])
sc.describe()
```

The `describe` function prints a summary of the StreamCollection, which groups the StationTraces within StationStreams, gives each StationTrace's identification information, and indicates if the StationStream/StationTrace is labeled as "passed" or "failed.

And the waveforms can be plotted by selecting the first (and only) StationStream with
```{code-cell} ipython3
---
render:
  image:
    height: 350px
---
import matplotlib.pyplot as plt
sta_st = sc[0]
sta_st.plot()
plt.close()
```

One convenient aspect of a StreamCollection is that it includes StationStream objects, and it is easy to access metadata, including the provenance of the data. 
We can print it's provenance information with the folling simple lines of code

```{code-cell} ipython3
print(sta_st[0].provenance.get_prov_dataframe())
```

You can also get the entire provenance document for all stations with

```{code-cell} ipython3
prov = workspace.get_provenance('nc72282711', labels=['default'])
print(prov)
```

Also, the printing dictionaries in python are not very readable in some cases.
So we can define a convenience function for this tutorial to make them easier to view
```{code-cell} ipython3
import json
import numpy as np
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

def print_dict(jdict):
    lines = json.dumps(jdict, indent=2, cls=NumpyEncoder).split("\n")
    for line in lines:
        print(line)
```

Note that the NumpyEncoder class is a solution from from 
[stackverflow](https://stackoverflow.com/questions/26646362/numpy-array-is-not-json-serializable) 
by user karlB.

If you want to inspect the rupture object for the event, it can be accessed with
```{code-cell} ipython3
rupt = workspace.get_rupture('nc72282711', label='default')
print_dict(rupt)
```

We can see that the rupture is represented as a dictionary with keys of "cells", "description", "reference", and "vertices".
In this case, we can see that this is rupture extent is was created by Jack Boatwright based on a finite fault slip inversion from Doug Dreger. 
These are the verticies that are used for computing finite fault distances.

The config file that was used for this event is a dictionary stored as a
[ruamel](https://yaml.readthedocs.io/en/latest/) object
that can be access as the `config` attribute to the workspace file.
```{code-cell} ipython3
type(workspace.config)
conf_dict = dict(workspace.config)
print(conf_dict.keys())
```

Here, we only print the "metrics" section to keep things simple.

```{code-cell} ipython3
print_dict(workspace.config["metrics"])
```

There are multiple ways to access the metrics from the StreamWorkspace.
For this tutorial, we will use the "WaveformMetricCollection" class:
```{code-cell} ipython3
from gmprocess.metrics.waveform_metric_collection import WaveformMetricCollection
wmc = WaveformMetricCollection.from_workspace(workspace, label='default')
print(wmc)
```

Printing the WaveformMetricCollection simply indicates that there is one station available in the small dataset for this tutorial.
We can see the attributes of the object that may be useful with

```{code-cell} ipython3
wmc.__dict__.keys()
```

Let's inspect the `waveform_metrics` attribute further.
First, we can see that it is a list with length one
```{code-cell} ipython3
print(type(wmc.waveform_metrics))
print(len(wmc.waveform_metrics))
```

The length is one because we only have one station in this dataset, and the waveform_metric list elements map to the stations.

And each element of the list is a WaveformMetricList object:
```{code-cell} ipython3
print(type(wmc.waveform_metrics[0]))
```

So let's select the first WaveformMetricList object and look at it
```{code-cell} ipython3
wml = wmc.waveform_metrics[0]
print(wml)
```

This summary indicates that there are 8 metrics in the WaveformMetricList for this station.
It also gives a quick summary of what each metric is, such as PGA.
For each metric, there are different values for each component (e.g., the as-recorded channels vs RotD50).

The constituent data within the WaveformMetricList is in the `metric_list` attribute
```{code-cell} ipython3
print(type(wml.metric_list))
print(wml.metric_list)
```

Each element in this list is a WaveformMetricType subclass
```{code-cell} ipython3
print(type(wml.metric_list[0]))
```

You can learn more about these class and their attributes by browsing the source code 
[here](https://code.usgs.gov/ghsc/esi/groundmotion-processing/-/blob/main/src/gmprocess/metrics/waveform_metric_type.py?ref_type=heads).
But for this tutorial, we will just convert them to a dictionary
```{code-cell} ipython3
pga_dict = wml.metric_list[0].to_dict()
print(pga_dict)
```

So, if we want to select the SA for the "h1" component, we have to write a loop to collect the values
```{code-cell} ipython3
sa = []
period = []
for metric in wml.metric_list:
    if metric.type != "SA":
        # We only want SA
        continue
    mdict = metric.to_dict()
    for comp, val in zip(mdict["components"], mdict["values"]):
        if comp.component_attributes["component_string"] == "h1":
            sa.append(val)
    period.append(mdict["metric_attributes"]["period"])
print(period)
print(sa)
```

And here you can see that there are only three periods conigured for the spectral acceleration calculation.
If a larger number of periods were specified in the config file, it would likely be useful to plot the SA as a fuction of period to see the response spectrum.



## The pyasdf interface

The ASDF data structure can be accessed directly from the StreamWorkspace object via the `dataset` attribute and print a summary of the ASDF object
```{code-cell} ipython3
ds = workspace.dataset
print(ds)
```

Alternatively, the ASDF object can be created directly with the pyasdf library
```{code-cell} ipython3
import pyasdf
ds = pyasdf.ASDFDataSet(data_path)
print(ds)
```

It is easy to get a list of the stations in the dataset
```{code-cell} ipython3
station_list = ds.waveforms.list()
print(station_list)
```

You can retrieve an obspy stream from the ASDF file by browsing the waveforms with knowledge of the stations, event ID, and labels. 
Note that ASDF uses a "tag" that combines the event ID and label.

```{code-cell} ipython3
---
render:
  image:
    height: 350px
---
station = station_list[0]
event_id  = "nc72282711"
label = "default"
tag = f"{event_id}_{label}"
st = ds.waveforms[station][tag]
print(st)
st.plot();
```

The [pyasdf](https://seismicdata.github.io/pyasdf/) library provides a lot more functionality than this, and we refer users to their documentation for additional details and examples.

## The h5py interface

Of the three options that we discuss in this tutorial, the "lowest level" interface to the ASDF file is to read it in as an HDF5 object:
```{code-cell} ipython3
import h5py
h5 = h5py.File(data_path, "r+")
print(h5)
```
The HDF5 standard is extremely flexible and is composed of three essential ingredients: "datasets", "groups", and "attributes".
Datasets are multidimensional arrays, groups are conceptually similar to directories on a file system or dictionary keys, and attributes are metadata associated with datasets or groups. 
The format is hierarchical because groups can contain other groups and/or datasets. 

You can use the `keys` method to see group keys:
```{code-cell} ipython3
h5.keys()
```

To demonstrate how to access the value of a group key, we will use the QuakeML entry:
```{code-cell} ipython3
print(h5["QuakeML"])
```

And we can see that this is a dataset.
To see the data in the dataset we can use the `[:]` operator:
```{code-cell} ipython3
print(h5["QuakeML"][:])
```

And it is not immediately clear how to interpret these numbers.
While pyasdf has functions for more easily parsing the data, if we are using the h5py objects it is useful to use the [ASDF definition ](https://asdf-definition.readthedocs.io/en/latest/events.html)
to help us understand how to parse the data.
From the ASDF definition, we see that the QuakeML dataset is a binary dump of a QuakeML file.

So we can create an in-memory binary stream of the data with the io library
```{code-cell} ipython3
import io
bytes = io.BytesIO(h5["QuakeML"][:])
```

And then we can hand this off to obspy's `read_events` method

```{code-cell} ipython3
import obspy
catalog = obspy.read_events(bytes)
print(catalog)
```

