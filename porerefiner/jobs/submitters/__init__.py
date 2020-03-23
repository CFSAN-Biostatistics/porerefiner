from abc import ABCMeta, abstractmethod
from typing import Union

from tempfile import mkdtemp
from pathlib import Path

import logging
import pkgutil

from porerefiner.cli_utils import render_dataclass, Email, Url, PathStr

SUBMITTERS = [] # configured (reified) submitters

REGISTRY = {} # available submitter classes

log = logging.getLogger('porerefiner.submitter.registry')

class _MetaRegistry(type):

    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        if cls not in REGISTRY:
            REGISTRY[name] = cls
        return cls

    def __call__(cls, *args, **kwargs):
        the_instance = super().__call__(*args, **kwargs)
        SUBMITTERS.append(the_instance)
        log.debug(cls.__name__)
        return the_instance

class RegisteringABCMeta(ABCMeta, _MetaRegistry):
    pass

class Submitter(metaclass=RegisteringABCMeta):

    def __repr__(self):
        return type(self).__name__

    @abstractmethod
    async def test_noop(self) -> None:
        "No-op method submitters should implement to make sure the submitter can access an external resource."
        pass

    @abstractmethod
    def reroot_path(self, path) -> Path:
        "Submitters should translate paths to execution environment"
        pass

    def _submit(self, job):
        "Create datadir, delegate job setup, then call subclass method to submit job"
        from porerefiner.jobs import FileJob, RunJob
        run = job.run
        file = job.file
        logg = log.getChild(type(self).__name__)
        hints = {}
        datadir = job.datadir = Path(mkdtemp())
        remotedir = job.remotedir = self.reroot_path(datadir)
        job.save()
        if isinstance(job.job_state, RunJob):
            cmd = job.job_state.setup(run, datadir)
        elif isinstance(job, FileJob):
            cmd = job.job_state.setup(file, file.run, datadir)
        if isinstance(cmd, tuple): #some jobs return a string plus execution hints
            cmd, hints = cmd
        cmd = " ".join(cmd.split()) # turn tabs and returns into spaces
        logg.getChild('cmd').critical(cmd)
        try:
            job.job_id = self.begin_job(cmd, datadir)
            job.status = 'QUEUED'
        except Exception as e:
            logg.error(e)
            job.job_state.attempts += 1
            if job.job_state.attempts > 3:
                job.status = 'FAILED'
                raise
        finally:
            job.save()



    @abstractmethod
    async def begin_job(self, execution_string, datadir, remotedir, environment_hints={}) -> str:
        "Semantics of scheduling a job"
        pass

    def _poll(self, job):
        logg = log.getChild(type(self).__name__)
        try:
            job.status = status = self.poll_job(job)
            logg.getChild(type(job.job_state).__name__).getChild(job.job_id).critical(status)
        except Exception as e:
            job.status = 'FAILED'
            logg.getChild(type(job.job_state).__name__).getChild(job.job_id).error(e)
            raise
        finally:
            job.save()


    @abstractmethod
    async def poll_job(self, job) -> str:
        pass

    def _close(self, job):
        logg = log.getChild(type(self).__name__)
        self.closeout_job

    @abstractmethod
    def closeout_job(self, job, datadir, remotedir) -> None:
        pass

    @classmethod
    def get_configurable_options(cls):
        "Enumerate configurable options and value type as a guide to configuration."
        return render_dataclass(cls)

