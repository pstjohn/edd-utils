# EDD Utils
This package is a utility for downloading Experiment Data Depot study instances through python or the commandline. It can be installed on your system through pip via the command

```console
pip install edd-utils

```

The package has two entry points, either as a commandline utility or as a python module. The commandline utility is used as below:

```console
zak@JBEI:~$ export_edd_study my_edd_study_slug --username my_edd_username --server my.edd.server.org
```

For an example of how to use the python module see the jupyter notebook in the notebooks directory.