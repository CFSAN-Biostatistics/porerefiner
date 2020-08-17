from unittest import TestCase, skip

import porerefiner.jobs as jobs
import porerefiner.jobs.submitters as submitters

from tests import TestJob, TestSubmitter


class TestJobBaseClasses(TestCase):

    def test_class_import(self):
        self.assertGreater(len(jobs.REGISTRY), 1)

    @skip('not yet implemented')
    def test_file_job_base_class(self):
        assert False

    @skip('not yet implemented')
    def test_run_job_base_class(self):
        assert False


    def test_job_singleton(self):
        job = TestJob(submitter=TestSubmitter()) # init the singleton
        assert job._the_instance == job
        assert TestJob._the_instance == job # prove that the class retains a reference to the singleton
        assert job == jobs.REGISTRY['TestJob']() # prove that you can now look up the singleton
        assert job == jobs.REGISTRY['TestJob'](submitter=None) # prove that its not re-initialized
        assert job.submitter != None # prove that state didn't change


class TestSubmitterBaseClass(TestCase):

    # @skip('not yet implemented')
    def test_submitter(self):
        t = TestSubmitter()
        assert t
        assert t in submitters.SUBMITTERS
