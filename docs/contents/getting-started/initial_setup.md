# Initial Setup

The initial setup includes two steps: Project setup, and STREC setup.

```{admonition} New in version 2.1
:class: note

The use of projects is optional.
If you do not wish to use projects, you need to specify the `confdir` and `datadir` command line arguments when calling the `gmrecords` command.
```

## Project setup

In order to simplify the command line interface, the `gmrecords` command makes use of "projects".
You can have many projects configured on your system, and a project can have data from many events.
A project is essentially a way to encapsulate the configuration and data directories so that they do not need to be specified as command line arguments.

There are two different types of configuration for projects:

**directory projects**
  Directory projects work by checking the current working directory for a projects configuration file that holds the data and configuration info.
  Thus, in order to use the projects, you have to be in that specific directory.
  Whenever you are in a directory with a projects configuration, those projects are available; system-level projects are not available.

**system-level projects**
  System-level projects work by checking the user's home directory for a project configuration file (`~/.gmprocess/projects.conf`) that can hold many different configured projects.
  When you use system-level projects, the projects are available from any directory on your system that does not contain a local projects configuration.

:::{attention}
See the [Configuration File](../manual/config_file) section for more information on how configuration options work.
:::

When you create either type of projects configuration, you will be prompted to include your name and email.
This information is used for the data provenance.
This facilitates reproducibility and giving credit to people processing data.
If you do not wish to share your personal information, we recommend using an institution or project name.

To create a directory projects configuration, use the gmrecords `init` subcommand in the directory where you would like to host projects.

```{code-block}
$ gmrecords init
Please enter a project title: [default]
Please enter the conf: [./conf]
Please enter the data: [./data]
Please enter your name and email. This information will be added
to the config file and reported in the provenance of the data
processed in this project.
	Name: Jane
	Email address: jane@mail.org

Created Project: default **Current Project**
	Conf Path: /Users/jane/tmp/gmprocess2/conf
	Data Path: /Users/jane/tmp/gmprocess2/data
```

The `projects` subcommand is used for managing system-level projects.
The arguments are

```{program-output} gmrecords projects -h
```

The [Command Line Interface](../tutorials/cli) tutorial provides an example of how to create system-level projects.

## STREC setup

[STREC](https://code.usgs.gov/ghsc/esi/strec) is the code for getting seismotectonic
information about an earthquake. This is used, for example, to select which ground 
motion model is appropriate. It is installed as a dependency, but the following
command needs to be run to to set up the config files and download relevant data:
```{code-block}
strec_cfg update [--datafolder /PATH/TO/STREC_DATA_DIR] --gcmt
```
Note that `/PATH/TO/STREC_DATA_DIR` can be any directory on your system that you
prefer. It will be used for storing the data that STREC uses.