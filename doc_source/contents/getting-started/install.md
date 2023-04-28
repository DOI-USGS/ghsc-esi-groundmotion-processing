# Installation

:::{important}
Our development team is not proficient with Windows systems, so our ability to support Windows installs is limited.
We have done our best to provide instructions to support Windows build.
:::


We recommend installing gmprocess into a virtual environment to isolate your code from other projects that might create conflicts in the dependencies.
You can use the Python3 [`venv`](https://docs.python.org/3/library/venv.html) module or [`conda`](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html) to create and manage virtual environments. If using `conda`, either [Anaconda](https://docs.anaconda.com/free/anaconda/install/index.html) or the more lightweight [Miniconda](https://docs.conda.io/en/latest/miniconda.html) can be used.
Conda generally uses more space on your filesystem, but it can install more dependencies.

Releases of gmprocess are available from [PyPi](https://pypi.org/project/gmprocess/) and [Conda-Forge](https://anaconda.org/conda-forge/gmprocess). 
The development version of gmprocess can be installed by cloning this repository. 
In either case, it is a good idea to review the [changelog](../developer/changelog) to keep track of any changes that you should be aware of. 

## Installing gmprocess Releases
If desired, create a virtual environment that runs a supported Python version. Supported Python versions can be found on the PyPi or Conda-Forge pages for gmprocess, or alternatively, by looking at `pyproject.toml`. To create an environment for gmprocess with `conda`, execute the following command in your terminal, answering `y` or `yes`, if prompted.

```
conda create --name gmprocess python=3.9

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

Note that PyPi wheels for the `fiona` dependency are not available for Windows and macOS arm64 architecture at the time this writing, so `pip` installations will fail. 
For these platforms, we recommend installing with `conda` because it can provide `fiona` builds.


### From Conda-Forge

```
conda install -c conda-forge gmprocess
```

## Installing from Source

:::{admonition} Prerequisites
:class: note

```{tab} Linux
- Bash shell, git, pip.

Most Linux distributions include these tools in the default installation.
```

```{tab} macOS
- Bash shell, git, pip.

The easiest way to install these tools is to install the XCode Command Line Tools.
Simply run `git`, and instructions for installing the Command Line Tools will be displayed if it is not installed.

Some PyPi wheels are not yet available for the macOS arm64 architecture.
As a result, some dependencies will be built from source when installing via `pip`.
Building the `fiona` package from source requires `GDAL`, which is a C++ library that can be installed manually or using conda.
```

```{tab} Windows
- [Miniconda](https://docs.conda.io/en/latest/miniconda.html#windows-installers) 
  (recommended) or [anaconda](https://www.anaconda.com/products/distribution).
- Git and some kind of console.

There is one dependency ([fiona](https://pypi.org/project/Fiona/)) that we have not been able to install with pip on Windows systems. So we rely on conda for this.
Start a conda session and run `conda init powershell`.
Then open a new powershell terminal and run `conda create --name gmprocess python=3.9 pip fiona` and `conda activate gmprocess`.
```

:::

First clone this repository and go into the root directory with

```
git clone https://code.usgs.gov/ghsc/esi/groundmotion-processing.git
cd groundmotion-processing
```

:::{admonition} Windows
:class: important
:::

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

## Tests

If you are installing from soruce and included the optional `test` dependencies in the install step, then you can run the unit tests in the root directory of the repository:

```
pytest .
```

This will be followed by a lot of terminal output.
Warnings are expected to occur and do not indicate a problem.
Errors indicate that something has gone wrong and you will want to troubleshoot.
You can create an issue in [GitHub](https://code.usgs.gov/ghsc/esi/groundmotion-processing/issues) if you are not able to resolve the problem.
