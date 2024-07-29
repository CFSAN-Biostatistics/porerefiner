# from unittest import TestCase, skip
from pytest import fixture, mark

import porerefiner.jobs as jobs
import porerefiner.jobs.submitters as submitters

from tests import JobClass, SubmitterClass

from dataclasses import dataclass




def test_class_import():
    assert len(jobs.CLASS_REGISTRY) > 1


def test_file_job_base_class(SubmitterClass):
    @dataclass
    class TestFileJob(jobs.FileJob):
        field: str
        def run(*a, **k):
            yield "",{}
    t = TestFileJob(submitter=SubmitterClass(), field="")
    assert t


def test_run_job_base_class(SubmitterClass):
    @dataclass
    class TestRunJob(jobs.RunJob):
        field: str
        def run(*a, **k):
            yield "",{}
            val = yield None
            print(val)
    t = TestRunJob(submitter=SubmitterClass(), field="")
    assert t

@mark.skip('not yet implemented')
def test_job_subclassing():
    assert False

@mark.skip("jobs aren't singletons anymore")
def test_job_singleton(SubmitterClass, JobClass):
    job = JobClass(submitter=SubmitterClass()) # init the class
    assert job._the_instance == job
    # assert TestJob._the_instance == job # prove that the class retains a reference to the singleton
    assert job == jobs.REGISTRY['TestJob'] # prove that you can now look up the singleton
    # assert job == jobs.REGISTRY['TestJob'](submitter=None) # prove that its not re-initialized
    assert job.submitter != None # prove that state didn't change


# @skip('not yet implemented')
def test_submitter():
    t = SubmitterClass()
    assert t
    assert t in submitters.SUBMITTERS
