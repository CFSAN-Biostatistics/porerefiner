from abc import ABCMeta, abstractmethod
from typing import Union

from tempfile import mkdtemp
from pathlib import Path

from porerefiner.jobs import FileJob, RunJob

import logging


REGISTRY = {}
SUBMITTER = None

log = logging.getLogger('porerefiner.jobs')

class _MetaRegistry(ABCMeta):

    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        if cls not in REGISTRY:
            REGISTRY[name] = (cls)
        return cls

    def __call__(cls, *args, **kwargs):
        global SUBMITTER
        if SUBMITTER:
            raise ValueError("Only one job submitter can be configured.")
        the_instance = SUBMITTER = super().__call__(*args, **kwargs)
        return the_instance

class Submitter(metaclass=_MetaRegistry):

    @abstractmethod
    def test_noop(self) -> None:
        "No-op method submitters should implement to make sure the submitter can access an external resource."
        pass

    @abstractmethod
    def reflect_path(self, path) -> Path:
        "Submitters should translate paths to execution environment"
        pass

    def _submit(self, run_or_file, job, run=None):
        "Create datadir, delegate job setup, then call subclass method to submit job"
        logg = log.getChild(type(self).__name__)
        hints = {}
        datadir = job.datadir = Path(mkdtemp())
        job.save()
        if isinstance(job.job_state, RunJob):
            cmd = job.job_state.setup(run_or_file, datadir)
        elif isinstance(job, FileJob):
            cmd = job.job_state.setup(run_or_file, run, datadir)
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

    @abstractmethod
    def closeout_job(self, job, datadir, remotedir) -> None:
        pass
