import asyncio

# from unittest import TestCase, skip
from unittest.mock import Mock, patch

from pytest import fixture, mark

import porerefiner.jobs
import porerefiner.jobs.submitters
import porerefiner.models as models

from porerefiner.jobs import submit_job, poll_active_job, poll_jobs

from tests import *
from hypothesis import given, settings, HealthCheck
from hypothesis.strategies import *

@mark.asyncio
@patch('porerefiner.jobs.submitters.logging')
@given(job=Model.Duties(),
        runn=Model.Runs())
@settings(suppress_health_check=(HealthCheck.too_slow,))
async def test_submit_job(log, db, job, runn):
    runn.save()
    job.run = runn
    job.save()
    assert job.run is not None
    assert await submit_job(job)

@mark.asyncio
@patch('porerefiner.jobs.logging')
@given(job=Model.Duties(),
        runn=Model.Runs())
@settings(suppress_health_check=(HealthCheck.too_slow,))
async def test_poll_active_job(log, db, job, runn):
    runn.save()
    job.run = runn
    job.save()
    assert job.id
    #raise TypeError(type(job).__name__)
    assert job.run is not None
    assert isinstance(job, models.Duty)
    assert await poll_active_job(job)

@mark.asyncio
@patch('porerefiner.jobs.logging')
@given(jobs=lists(Model.Duties()),
        runn=Model.Runs())
@settings(suppress_health_check=(HealthCheck.too_slow,))
async def test_poll_jobs(log, db, jobs, runn):
    runn.save()
    for job in jobs:
        job.run = runn
        job.save()
    result, _, _ = await poll_jobs(jobs, jobs)
    assert result == len(jobs) * 2