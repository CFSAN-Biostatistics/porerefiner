=======
History
=======

0.9.5 (2021-06-22)
------------------

* prfr CLI client now no longer tries to load service config.yaml; it has its own or you can give socket/host/ssl arguments at the command line.

0.9.4 (2021-03-18)
------------------

* Option in `prfr` to connect to remote Porerefiner hosts.

0.9.3 (2021-03-15)
------------------

* Bugfixes to tagging, other improvements

0.9.2 (2021-03-08)
------------------

* Bugfixes, small improvements

0.9.1b (2021-02-19)
-------------------

* Bugfix - package properly requires Python 3.8 now.

0.9.1 (2020-12-16)
------------------

* Added triple tags - namespace, name, value - to data model

* Protobuf API now accepts triple-tags along with new samples

* Added a way for plugins to define and register their own sample sheet parsers

0.9.0 (2020-09-14)
------------------

* Job system re-work. Plugins will need to be updated for compatibility.

* Jobs now expect generators (yield) instead of methods (return). This is to enable multi-step workflows.

* Generic job now should be configured with a list of commands, rather than a single command. (it can be a single-item list.)
 
0.8.21 (2020-08-24)
-------------------

* Bugfix for remote directory rerooting, new tests

0.8.20 (2020-08-20)
-------------------

* Bugfix and tests for config

0.8.19 (2020-08-20)
-------------------

* more convenient access of config from plugins

0.8.18 (2020-08-18)
-------------------

* new command to run jobs on sample data

0.8.17 (2020-08-17)
-------------------

* bugfixes for the bugfixes and more tests

0.8.16 (2020-08-17)
-------------------

* bunch of bug fixes in job system

0.8.15 (2020-08-06)
-------------------

* fixed bug where plugins wouldn't be imported

0.8.14 (2020-07-29)
-------------------

* fixed bug in job spawn/db fields of Path type

0.8.13 (2020-07-28)
-------------------

* changing log levels for some events; DEBUG now no longer jammed up by SQL spam

0.8.12 (2020-07-24)
-------------------

* bugfixes in sample sheet loading

0.8.11 (2020-07-15)
-------------------

* More platform-universal MD5 hashing of files on completion

0.8.10 (2020-07-15)
-------------------

* Bugfixes in model, barcode_id type

0.8.9 (2020-07-13)
------------------

* Bugfixes in ``prfr load``, sample sheet handling for v1.0.1 samplesheets (barcode kit id's)

0.8.8 (2020-07-01)
------------------

* Improved behavior on job creation; buxfixes in job submit step

0.8.7 (2020-05-21)
------------------

* Fixed a bug in ``porerefinerd verify``

0.8.6 (2020-05-18)
------------------

* Fixed a bug that would prevent the watchdog from starting

0.8.5 (2020-04-15)
------------------

* Samplesheet and data model now distinguish between sequencing and barcoding kits

0.8.4 (2020-03-23)
------------------

* New plugin architecture, combined with a cookiecutter definition for creating new ones
* Removed several in-progress job/submitter types to plugins

0.8.3 (2020-03-13)
------------------

* ``prfr`` now recognizes site config if user config doesn't exist

0.8.2 (2020-03-12)
------------------

* Fixed tests, general bugfixes

0.8.1 (2020-03-11)
------------------

* Improved service files.

0.8.0 (2020-03-09)
------------------

* First release on PyPI.
