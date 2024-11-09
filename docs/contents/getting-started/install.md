# Installation


We recommend installing gmprocess into a virtual environment to isolate your code from other projects that might create conflicts in the dependencies.
You can use the Python3 [`venv`](https://docs.python.org/3/library/venv.html) module or [`conda`](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html) to create and manage virtual environments. 
If using `conda`, either [Anaconda](https://docs.anaconda.com/free/anaconda/install/index.html) or the more lightweight [Miniconda](https://docs.conda.io/en/latest/miniconda.html) can be used.
Conda generally uses more space on your filesystem, but it can install more dependencies, including non-Python dependencies.

Releases of gmprocess are available from [PyPi](https://pypi.org/project/gmprocess/) and [Conda-Forge](https://anaconda.org/conda-forge/gmprocess). 
The development version of gmprocess can be installed by cloning this repository. 
In either case, it is a good idea to review the [changelog](../developer/changelog) to keep track of any changes that you should be aware of.

The `setup_env.sh` script automates the process for developers and is primarily intended for developers.
It creates a "gmprocess" virtual environment with conda and installs the code in editable mode from source with all of the optional dependencies. 

## Installing gmprocess Releases
If desired, create a virtual environment that runs a supported Python version. 
Supported Python versions can be found on the PyPi or Conda-Forge pages for gmprocess, or alternatively, by looking at `pyproject.toml`. 
To create an environment for gmprocess with `conda`, execute the following command in your terminal, answering `y` or `yes`, if prompted.

```
conda create --name gmprocess python=3.12
```

We'll then need to activate the virtual environment to proceed.

```
conda activate gmprocess
```

Now install gmprocess via your preferred package manager or from a source distribution

### From PyPi

```
pip install gmprocess
```

If you get an error message from pip that it can't install pyproj, we recommend installing `libgdal-netcdf` with conda in a virtual environment and then installing gmprocess as described above within that environment.

### From Conda-Forge

```
conda create --name gmprocess python=3.12
conda activate gmprocess
conda install -c conda-forge gmprocess
```

## Installing from Source

First clone this repository and go into the root directory with

```
git clone https://code.usgs.gov/ghsc/esi/groundmotion-processing.git
cd groundmotion-processing
```

Next, install the code with pip

```
pip install .
```

Note that this will install the minimum requirements to run the code.
There are additional optional packages that can be installed that support running the unit tests (`test`), code development (`dev`), building wheels (`build`), and building the documentation (`doc`).
To install these, you need to add the relevant option in brackets:

```
pip install .[test,dev,doc,build]
```

For developers, it is also convenient to install the code in "editable" mode by adding the `-e` option:

```
pip install -e .[test,dev,doc,build]
```

If you get an error message from pip that it can't install pyproj, we recommend installing `libgdal-netcdf` with conda in a virtual environment and then installing gmprocess as described above within that environment.

## Tests

If you are installing from source and included the optional `test` dependencies in the install step, then you can run the unit tests in the root directory of the repository:

```
pytest .
```

This will be followed by a lot of terminal output.
Warnings are expected to occur and do not indicate a problem.
Errors indicate that something has gone wrong and you will want to troubleshoot.
If you are not able to resolve the problem, you can create an issue in [GitHub](https://github.com/DOI-USGS/ghsc-esi-groundmotion-processing) or [Gitlab](https://code.usgs.gov/ghsc/esi/groundmotion-processing/issues) or email the developers at [gmprocess@usgs.gov](mailto:gmprocess@usgs.gov).
