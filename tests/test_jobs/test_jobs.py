import asyncio

from unittest import TestCase, skip
from unittest.mock import Mock, patch

import porerefiner.jobs
import porerefiner.jobs.submitters

from porerefiner.jobs import submit_job, poll_active_job, poll_jobs

from tests import *
from hypothesis import given
from hypothesis.strategies import *

def run(task):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(task)


class TestJobSubmission(TestCase):

    @patch('porerefiner.jobs.submitters.logging')
    @given(job=Model.Jobs())
    @with_database
    def test_submit_job(self, log, job):
        job.save()
        assert run(submit_job(job))

    @patch('porerefiner.jobs.logging')
    @given(job=Model.Jobs())
    @with_database
    def test_poll_active_job(self, log, job):
        job.save()
        assert run(poll_active_job(job))

    @patch('porerefiner.jobs.logging')
    @given(jobs=lists(Model.Jobs()))
    @with_database
    def test_poll_jobs(self, log, jobs):
        result, _, _ = run(poll_jobs(jobs, jobs))
        self.assertEqual(result, len(jobs) * 2)