import asyncio

from unittest import TestCase, skip
from unittest.mock import Mock, patch

import porerefiner.jobs as jobs
import porerefiner.jobs.submitters as submitters

from porerefiner.jobs import submit_job, poll_active_job, poll_jobs

from tests import *
from hypothesis import given
from hypothesis.strategies import *

def run(task):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(task)


class TestJobSubmission(TestCase):

    @patch('porerefiner.jobs.submitters.logging')
    @given(job=job_records())
    @with_database
    def test_submit_job(self, log, job):
        assert run(submit_job(job))

    @patch('porerefiner.jobs.logging')
    @given(job=job_records())
    @with_database
    def test_poll_active_job(self, log, job):
        assert run(poll_active_job(job))

    @patch('porerefiner.jobs.logging')
    @given(jobs=lists(job_records()))
    @with_database
    def test_poll_jobs(self, log, jobs):
        result, _, _ = run(poll_jobs(jobs, jobs))
        self.assertEqual(result, len(jobs) * 2)