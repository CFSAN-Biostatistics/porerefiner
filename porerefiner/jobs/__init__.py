from abc import ABCMeta, abstractmethod, ABC
from collections import namedtuple
from dataclasses import dataclass

from .submitters import Submitter
from porerefiner.models import Job, File, Run
from porerefiner.cli_utils import render_dataclass, Email, Url, PathStr
from pathlib import Path
from typing import Union, Tuple

import logging
import pkgutil

log = logging.getLogger('porerefiner.job.registry')

async def poll_active_job(job):
    await job.job_state.submitter._poll(job)
    return 1

async def submit_job(job):
    job.job_state.submitter._submit(job)
    return 1

async def complete_job(job):
    job.job_state.submitter._close(job)
    return 1

async def poll_jobs():
    jobs_polled = 0
    jobs_submitted = 0
    jobs_collected = 0
    for job in Job.select().where(Job.status == 'READY'):
        jobs_submitted += await submit_job(job)
        jobs_polled += 1
    for job in Job.select().where(Job.status == 'RUNNING'):
        jobs_collected += await poll_active_job(job)
        jobs_polled += 1
    return jobs_polled, jobs_submitted, jobs_collected

JOBS = namedtuple('JOBS', ('FILES', 'RUNS'), defaults=([], []))() #configured (reified) job instances

REGISTRY = {} # available job classes

class _MetaRegistry(type):

    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        if cls not in REGISTRY:
            REGISTRY[name] = cls
        return cls

    def __call__(cls, *args, **kwargs):
        try:
            the_instance = super().__call__(*args, **kwargs)
        except TypeError as e:
            raise TypeError(f"Bad config: {cls.__name__}: {e} ({args}, {kwargs})") from e
        if isinstance(the_instance, FileJob):
            JOBS.FILES.append(the_instance)
            log.getChild('files').debug(cls.__name__)
        if isinstance(the_instance, RunJob):
            JOBS.RUNS.append(the_instance)
            log.getChild('runs').debug(cls.__name__)
        return the_instance

class RegisteringABCMeta(ABCMeta, _MetaRegistry):
    pass

@dataclass
class AbstractJob(metaclass=RegisteringABCMeta):
    submitter: Submitter

    @classmethod
    def get_configurable_options(cls):
        "Enumerate configurable options and value type as a guide to configuration."
        return render_dataclass(cls)


class FileJob(AbstractJob):

    @abstractmethod
    def setup(self, run: Run, file: File, datadir: Path, remotedir: Path) -> Union[str, Tuple[str, dict]]:
        pass

    @abstractmethod
    def collect(self, run: Run, file: File, datadir: Path, pid: Union[str, int]) -> None:
        pass

class RunJob(AbstractJob):

    @abstractmethod
    def setup(self, run: Run, datadir: Path, remotedir: Path) -> Union[str, Tuple[str, dict]]:
        pass

    @abstractmethod
    def collect(self, run: Run, datadir: Path, pid: Union[str, int]) -> None:
        pass



for loader, module_name, is_pkg in  pkgutil.walk_packages(__path__):
    _module = loader.find_module(module_name).load_module(module_name)
    # globals()[module_name] = _module
