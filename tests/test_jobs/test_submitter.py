from tests import *

from pytest import mark

# from unittest import TestCase

import porerefiner.jobs.submitters as subs

from hypothesis import given


@mark.asyncio
@given(job_rec = Model.Duties(),
        job_code = jobs(),
        run = Model.Runs())
async def test_submit(db, job_rec, job_code, run):
    run.save()
    job_rec.run = run
    job_rec.save()
    await job_code.submitter._submit(job_rec)