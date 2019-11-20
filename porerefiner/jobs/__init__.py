from abc import ABCMeta, abstractmethod, ABC
from collections import namedtuple

from porerefiner.models import Job, File, Run
from pathlib import Path
from typing import Union, Tuple

import logging
import pkgutil

async def create_jobs_for_file(file):
    pass

async def create_jobs_for_run(run):
    pass

async def poll_active_job(job):
    pass

async def submit_job(job):
    return 1

async def complete_job(job):
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

JOBS = namedtuple('JOBS', ('FILES', 'RUNS'), defaults=([], []))()

REGISTRY = {}

class _MetaRegistry(ABCMeta):

    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        if cls not in REGISTRY:
            REGISTRY[name] = (cls)
        return cls

    def __call__(cls, *args, **kwargs):
        try:
            the_instance = super().__call__(*args, **kwargs)
        except TypeError as e:
            raise TypeError(f"{cls.__name__}: {e} ({args}, {kwargs})") from e
        if isinstance(the_instance, FileJob):
            JOBS.FILES.append(the_instance)
        if isinstance(the_instance, RunJob):
            JOBS.RUNS.append(the_instance)
        the_instance.attempts = 0
        return the_instance

class AbstractJob(ABC):
    pass


class FileJob(AbstractJob, metaclass=_MetaRegistry):

    @abstractmethod
    def setup(self, run: Run, file: File, datadir: Path, remotedir: Path) -> Union[str, Tuple[str, dict]]:
        pass

    @abstractmethod
    def collect(self, run: Run, file: File, datadir: Path, pid: Union[str, int]) -> None:
        pass

class RunJob(AbstractJob, metaclass=_MetaRegistry):

    @abstractmethod
    def setup(self, run: Run, datadir: Path, remotedir: Path) -> Union[str, Tuple[str, dict]]:
        pass

    @abstractmethod
    def collect(self, run: Run, datadir: Path, pid: Union[str, int]) -> None:
        pass


for loader, module_name, is_pkg in  pkgutil.walk_packages(__path__):
    _module = loader.find_module(module_name).load_module(module_name)
    globals()[module_name] = _module
