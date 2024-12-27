#!/bin/bash

VENV=gmprocess
PYVER=3.12
cwd=$(pwd)
echo "Installing ${VENV}...${cwd}"

unamestr=`uname`
if [ "$unamestr" == 'Linux' ]; then
    prof=~/.bashrc
    matplotlibdir=~/.config/matplotlib
elif [ "$unamestr" == 'FreeBSD' ] || [ "$unamestr" == 'Darwin' ]; then
    prof=~/.bash_profile
    matplotlibdir=~/.matplotlib
else
    echo "Unsupported environment. Exiting."
    exit
fi

source $prof

echo "Path:"
echo $PATH

# create a matplotlibrc file with the non-interactive backend "Agg" in it.
if [ ! -d "$matplotlibdir" ]; then
    mkdir -p $matplotlibdir
fi
matplotlibrc=$matplotlibdir/matplotlibrc
if [ ! -e "$matplotlibrc" ]; then
    echo "backend : Agg" > "$matplotlibrc"
    echo "NOTE: A non-interactive matplotlib backend (Agg) has been set for this user."
elif grep -Fxq "backend : Agg" $matplotlibrc ; then
    :
elif [ ! grep -Fxq "backend" $matplotlibrc ]; then
    echo "backend : Agg" >> $matplotlibrc
    echo "NOTE: A non-interactive matplotlib backend (Agg) has been set for this user."
else
    sed -i '' 's/backend.*/backend : Agg/' $matplotlibrc
    echo "NOTE: $matplotlibrc has been changed to set 'backend : Agg'"
fi


# Is conda installed?
conda --version
if [ $? -ne 0 ]; then
    echo "No conda detected, installing miniconda..."

    command -v curl >/dev/null 2>&1 || { echo >&2 "Script requires curl but it's not installed. Aborting."; exit 1; }

    miniforge_url="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
    curl -L $miniforge_url -o miniforge.sh &>/dev/null

    # if miniforge.sh fails, bow out gracefully
    if [ $? -ne 0 ];then
        echo "Failed to run miniconda installer shell script. Exiting."
        exit 1
    fi

    echo "Install directory: $HOME/miniconda"

    bash miniforge.sh -f -b -p $HOME/miniconda

    # Need this to get conda into path
    . $HOME/miniconda/etc/profile.d/conda.sh

    rm miniforge.sh
else
    echo "conda detected, installing $VENV environment..."
fi

# Update the conda tool
CVNUM=`conda -V | cut -f2 -d' '`
LATEST=`conda search conda | tail -1 | tr -s ' ' | cut -f2 -d" "`
echo "${CVNUM}"
echo "${LATEST}"
if [ ${LATEST} != ${CVNUM} ]; then
    echo "##################Updating conda tool..."
    CVERSION=`conda -V`
    echo "Current conda version: ${CVERSION}"
    conda update -n base -c defaults conda -y
    CVERSION=`conda -V`
    echo "New conda version: ${CVERSION}"
    echo "##################Done updating conda tool..."
else
    echo "conda ${CVNUM} already matches latest version ${LATEST}. No update required."
fi

# only add this line if it does not already exist
grep "/etc/profile.d/conda.sh" $prof
if [ $? -ne 0 ]; then
    echo ". $_CONDA_ROOT/etc/profile.d/conda.sh" >> $prof
fi

# Set libmamba as solver
conda config --set solver libmamba &>/dev/null

# Start in conda base environment
echo "Activate base virtual environment"
conda activate base

# Create a conda virtual environment
echo "Creating the $VENV virtual environment:"
conda create -y -n $VENV -c conda-forge python=$PYVER


# Bail out at this point if the conda create command fails.
if [ $? -ne 0 ]; then
    echo "Failed to create conda environment.  Resolve any conflicts, then try again."
    exit
fi

# Activate the new environment
echo "Activating the $VENV virtual environment"
conda activate $VENV

# Do mac-specific conda installs
if [ "$unamestr" == 'FreeBSD' ] || [ "$unamestr" == 'Darwin' ]; then
    # This is motivated by the mysterious pyproj/rasterio error and incorrect results
    # that only happen on ARM macs. 
    # https://github.com/conda-forge/pyproj-feedstock/issues/156
    conda install -c conda-forge -y libgdal-netcdf
fi

# Install this package
cd "${cwd}"
echo "Installing ${VENV}...${cwd}"
pip install -e .[dev,test,doc,build]

# Tell the user they have to activate this environment
echo "Type 'conda activate $VENV' to use this new virtual environment."
