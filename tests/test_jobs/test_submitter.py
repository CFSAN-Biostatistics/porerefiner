from tests import _run
from tests import *

from unittest import TestCase

import porerefiner.jobs.submitters as subs

from hypothesis import given

class TestSubmitters(TestCase):

    @given(job_rec = Model.Duties(),
           job_code = jobs(),
           run = Model.Runs())
    @with_database
    def test_submit(self, job_rec, job_code, run):
        run.save()
        job_rec.run = run
        job_rec.save()
        _run(job_code.submitter._submit(job_rec))