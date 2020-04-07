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

What is it?
-----------

You install it on your GridION. It watches the data output directory and notes the creation and modification of sequencing output files. You can attach sample sheets to runs, for instance when you're multiplexing samples - the MinKnow software is agnostic to sample membership in libraries, so maybe you want something to keep track of that. Then when the run completes (is idle for a period of time) a series of configurable events are triggered. That's often pretty useful for, let's say, sending data to your LIMS or through some kind of biosurveillance pipeline.

Installation
------------

PoreRefiner is available as a Python package:

::

    pip install porerefiner

Porerefiner can be started as a simple UNIX daemon:

::

    porerefinerd start --daemonize

but also includes service unit files for administration via ``systemctl``.

Copy the files ``porerefiner.service`` and ``porerefiner.app.service`` from the package to systemd:

::

    cp /usr/local/lib/python3.7/dist-packages/porerefiner/porerefiner.service /lib/systemd/system
    cp /usr/local/lib/python3.7/dist-packages/porerefiner/porerefiner.app.service /lib/systemd/system
    systemctl enable porerefiner.service
    systemctl enable porerefiner.app.service

Once the package is installed, ``porerefinerd`` and ``prfr`` should be on your path. You can use ``porerefinerd init`` to set up the config file for the porerefiner service, it will prompt you for the save locations of the database, the local socket, nanopore's output directory, and where the config file should be saved:

::

    $ porerefinerd init
    create PoreRefiner config at /etc/porerefiner/config.yaml? [y/N]: y
    location of porerefiner RPC socket? [/etc/porerefiner/porerefiner.sock]:
    location of database? [/etc/porerefiner/database.db]:
    nanopore data output location?: /data
    export POREREFINER_CONFIG="/etc/porerefiner/config.yaml"

Then you can start the porerefiner services:

::

    systemctl start porerefiner.service
    systemctl start porerefiner.app.service

If you wish to enable the PoreRefiner web interface, you should ensure that port 8844 is reachable from remote hosts.

Writing Plugins
---------------

PoreRefiner has a plugin architecture; pip-installable Python packages can make themselves known to PoreRefiner using entry_points in ``setup.py``. The easiest way to write your own plugin notifiers, jobs, and submitters for PoreRefiner is to use the cookiecutter template:

::

    $ cookiecutter https://github.com/CFSAN-Biostatistics/new-porerefiner-plugin
    project_name [My Porerefiner Plugin]:
    project_slug [my_porerefiner_plugin]:
    project_short_description [This is a plugin for Porerefiner, a tool for managining Nanopore sequencing.]:

See the Cookiecutter docs: https://cookiecutter.readthedocs.io/en/1.7.0/

Cookiecutter will create a full project repo and stub classes for your plugin. Open ``<project_slug>/<project_slug>/<project_slug>.py`` and you can fill in the method code blocks to implement the various functions of the necessary interfaces.

Notifiers
=========

Notifiers are "fire and forget" handlers for "end-of-run" events; when an hour has elapsed since the last modification of a file in a run (or whatever idle time is configured in ``config.yaml``, the configured notifiers will be fired off with the run event. Out of the box, PoreRefiner comes with three notifiers - a notifier to send OS-based popup "toast" notifications (if ``pynotifier`` is installed), a notifier to make an HTTP request to a defined endpoint, and a notifier to send a message into an Amazon Web Services Simple Queue Service (SQS) queue. Notifiers differ from jobs in that they're assumed to run quickly/instantly and therefore they're executed synchronously. As a result a long-running notifier can hang the software. For tasks that can't execute quickly (copying files, etc), use a job.

Jobs
====

Jobs are processes that are assumed to take longer to execute and thus should execute asynchronously. As a result the job handler interface is more complex, and jobs require submitters to execute to (described below.) Jobs can be triggered either on the idle timeout of an individual file, or of the entire run, simply by extending the appropriate superclass - `FileJob` and `RunJob`. The PoreRefiner software will dispatch the correct configured job type, collect any type of process or job ID that is returned, and periodically poll the job's submitter for completion status. A run's in-progress jobs can be viewed through the ``prfr`` tool.

Submitters
==========

Submitters are the interface between jobs and the execution system. For instance, the ``HpcSubmitter`` knows how to use SSH to execute commands on a typical HPC using ``qsub``. PoreRefiner has an additional ``LocalSubmitter`` which simply runs commands locally, in a subprocess.

Here's an example of a simple post-run workflow configuration using the generic file job and the local submitter:

::

    submitters:
    - class: LocalSubmitter
      jobs:
      - class: GenericFileJob
        config:
          command: cp {file.path} /network/output/{run.name}/{file.name}

More examples to come in the Porerefiner Config Cookbook:

https://github.com/crashfrog/porerefiner-config-cookbook

If you develop a useful or interesting config, please consider contributing it to the cookbook using a pull request.




Using this software
-------------------

``prfr`` is the end-user client; Minion users should use this tool to monitor runs in progress, load sample sheets, and tag runs and samples.

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

If the web service is enabled, users can also upload and attach sample sheets using the web interface.


Administration
--------------

When the PoreRefiner service ``porerefinerd`` is stopped, it has a number of administrative functions:

::

    $ porerefinerd --help
    Usage: porerefiner.py [OPTIONS] COMMAND [ARGS]...

    Options:
    --help  Show this message and exit.

    Commands:
    init    Find the Nanopore output directory and create the config file.
    list    List job system stuff.
    reset   Utility function to reset various state.
    start   Start the PoreRefiner service.
    verify  Run various checks.

::

    $ porerefinerd init --help
    Usage: porerefiner.py init [OPTIONS]

    Find the Nanopore output directory and create the config file.

    Options:
    --config TEXT
    --nanopore_dir TEXT
    --help               Show this message and exit.

::

    $ porerefinerd list --help
    Usage: porerefiner.py list [OPTIONS] COMMAND [ARGS]...

    List job system stuff.

    Options:
    --help  Show this message and exit.

    Commands:
    jobs        List the configurable and configured jobs.
    notifiers   List the configurable and configured notifiers.
    submitters  List the configureable and configured submitters.

::

    $ porerefinerd reset --help
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

    $ porerefinerd verify --help
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
