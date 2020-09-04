import asyncio

from unittest import TestCase, skip
from unittest.mock import Mock, patch

import porerefiner.jobs
import porerefiner.jobs.submitters
import porerefiner.models as models

from porerefiner.jobs import submit_job, poll_active_job, poll_jobs

from tests import *
from hypothesis import given, settings, HealthCheck
from hypothesis.strategies import *

def run(task):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(task)


class TestJobSubmission(TestCase):

    @patch('porerefiner.jobs.submitters.logging')
    @given(job=Model.Duties(),
           runn=Model.Runs())
    @settings(suppress_health_check=(HealthCheck.too_slow,))
    @with_database
    def test_submit_job(self, log, job, runn):
        runn.save()
        job.run = runn
        job.save()
        assert job.run is not None
        assert run(submit_job(job))

    
    @patch('porerefiner.jobs.logging')
    @given(job=Model.Duties(),
           runn=Model.Runs())
    @settings(suppress_health_check=(HealthCheck.too_slow,))
    @with_database
    def test_poll_active_job(self, log, job, runn):
        runn.save()
        job.run = runn
        job.save()
        assert job.pk
        #raise TypeError(type(job).__name__)
        assert job.run is not None
        assert isinstance(job, models.Duty)
        assert run(poll_active_job(job))

    
    @patch('porerefiner.jobs.logging')
    @given(jobs=lists(Model.Duties()),
           runn=Model.Runs())
    @settings(suppress_health_check=(HealthCheck.too_slow,))
    @with_database
    def test_poll_jobs(self, log, jobs, runn):
        runn.save()
        for job in jobs:
            job.run = runn
            job.save()
        result, _, _ = run(poll_jobs(jobs, jobs))
        self.assertEqual(result, len(jobs) * 2)