from tests import _run
from tests import *

from unittest import TestCase

import porerefiner.jobs.submitters as subs

from hypothesis import given

class TestSubmitters(TestCase):

    @given(job_rec = Model.Jobs(),
           job_code = jobs())
    @with_database
    def test_submit(self, job_rec, job_code):
        _run(job_code.submitter._submit(job_rec))