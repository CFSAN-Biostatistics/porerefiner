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

    @given(job=job_records())
    def test_submit_job(self, job):
        assert run(submit_job(job))

    @given(job=job_records())
    def test_poll_active_job(self, job):
        assert run(poll_active_job(job))

    @given(jobs=lists(job_records()))
    def test_poll_jobs(self, jobs):
        result, _, _ = run(poll_jobs(jobs, jobs))
        self.assertEquals(result, len(jobs) * 2)