from unittest import TestCase, skip

import porerefiner.jobs as jobs
import porerefiner.jobs.submitters as submitters


class TestJobBaseClasses(TestCase):

    def test_class_import(self):
        self.assertGreater(len(jobs.REGISTRY), 1)

    @skip('not yet implemented')
    def test_file_job_base_class(self):
        assert False

    @skip('not yet implemented')
    def test_run_job_base_class(self):
        assert False


class TestSubmitterBaseClass(TestCase):

    @skip('not yet implemented')
    def test_submitter(self):
        assert False
