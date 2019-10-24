===========
PoreRefiner
===========


.. image:: https://img.shields.io/pypi/v/porerefiner.svg
        :target: https://pypi.python.org/pypi/porerefiner

.. image:: https://img.shields.io/travis/crashfrog/porerefiner.svg
        :target: https://travis-ci.org/crashfrog/porerefiner

.. image:: https://readthedocs.org/projects/porerefiner/badge/?version=latest
        :target: https://porerefiner.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status




To help you manage your pores


* Free software: MIT license
* Documentation: https://porerefiner.readthedocs.io.


Introduction
------------

PoreRefiner is a software tool to watch Nanopore runs in progress and attach sample information to them, as well as provide an interface for integration with LIMS services and other online systems. It supports both push and pull modalities for data exchange with those systems - push, via a series of configurable notifiers, and pull, via a simple Flask webservice and a Protobuf RPC service. It also includes a command-line interface for working with the run database.

Installation
------------

PoreRefiner is available as a Python package:

::
pip install porerefiner

Using this software
-------------------
::
$ prfr
Usage: prfr [OPTIONS] COMMAND [ARGS]...

  Command line interface for PoreRefiner, a Nanopore integration toolkit.

Options:
  --help  Show this message and exit.

Commands:
  info      Return information about a run, historical or in progress.
  load      Load a sample sheet to be attached to a run, or to the next run...
  proto     Append to the notifiers section of the config a default config...
  ps        Show runs in progress, or every tracked run (--all).
  rm        Remove a run and recover hard drive space.
  template  Write a sample sheet template to STDOUT.


Features
--------

Automatic detection of runs in progress

Sample sheet and sample tracking through the flowcell/run context, and beyond

How it works
------------

PoreRefiner uses fsevents to detect filesystem events during a Nanopore run, including the creating of new directories in the Nanopore output folder. Flowcells, runs, and run files can be detected this way. PoreRefiner will update a SQLite database with run information, including what it's able to pull out of Minknow.

If all of the files of a run have not been modified in an hour, PoreRefiner will mark a completion time for that run. If any of the files in a run have not been modified in an hour, they may be picked up by the Job runner for some subsequent processing.

PoreRefiner presents many interfaces to address integration challenges:

A CLI interface for both human use and simple scripting

A simple HTTP service for communication with LIMS and other services

A Protobuf-RPC service for inter-process communication (Protobuf bindings are available in Python, C, JavaScript, Java, and many other languages)

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
