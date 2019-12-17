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

    $ prfr --help
    Usage: prfr [OPTIONS] COMMAND [ARGS]...

      Command line interface for PoreRefiner, a Nanopore run manager.

    Options:
    --help  Show this message and exit.

    Commands:
    info      Return information about a run, historical or in progress.
    load      Load a sample sheet to be attached to a run, or to the next run...
    ps        Show runs in progress, or every tracked run (--all), or with a...
    tag       Add one or more tags to a run.
    template  Write a sample sheet template to STDOUT.
    untag     Remove one or more tags from a run.


Administration
--------------

When the PoreRefiner service is stopped, it has a number of administrative functions:

::

    $ python -m porerefiner.porerefiner --help
    Usage: porerefiner.py [OPTIONS] COMMAND [ARGS]...

    Options:
    --help  Show this message and exit.

    Commands:
    list    List job system stuff.
    reset   Utility function to reset various state.
    start   Start the PoreRefiner service.
    verify  Run various checks.

::

    $ python -m porerefiner.porerefiner list --help
    Usage: porerefiner.py list [OPTIONS] COMMAND [ARGS]...

    List job system stuff.

    Options:
    --help  Show this message and exit.

    Commands:
    jobs        List the configurable and configured jobs.
    notifiers   List the configurable and configured notifiers.
    submitters  List the configureable and configured submitters.

::

    $ python -m porerefiner.porerefiner reset --help
    Usage: porerefiner.py reset [OPTIONS] COMMAND [ARGS]...

    Utility function to reset various state.

    Options:
    --help  Show this message and exit.

    Commands:
    config        Reset config to defaults.
    database      Reset database to empty state.
    jobs          Reset all jobs to a particular status.
    runs          Reset all runs to in-progress status.
    samplesheets  Clear samplesheets that aren't attached to any run.

::

    $ python -m porerefiner.porerefiner verify --help
    Usage: porerefiner.py verify [OPTIONS] COMMAND [ARGS]...

    Run various checks.

    Options:
    --help  Show this message and exit.

    Commands:
    notifiers   Verify notifiers by sending notifications.
    submitters  Verify configuration of job submitters by running their tests.


Features
--------

Automatic detection of runs in progress

Sample sheet and sample tracking through the flowcell/run context, and beyond

Schedule automatic analysis of runs and files in AWS or your HPC

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
