
from unittest import TestCase, skip

from tests import paths, TestBase

from porerefiner import models

from hypothesis import given, strategies as strat
#from hypothesis_fspaths import fspaths, _PathLike

from datetime import datetime
import pathlib

# SQLite can't accept a 32-bit integer
sql_ints = lambda: strat.integers(min_value=-2**16, max_value=2**16)

# safe_paths = lambda: fspaths().filter(lambda x: isinstance(x, str) or isinstance(x, _PathLike))



class TestModels(TestBase):

    @given(paths())
    def test_path_field(self, path):
        #path = str(path)
        fld = models.PathField()
        self.assertEqual(fld.python_value(fld.db_value(path)), pathlib.Path(path))

    def test_models_registered(self):
        self.assertEqual(len(models.REGISTRY), 9)

    @given(tag=strat.text().filter(lambda x: x))
    def test_tags(self, tag):
        flow = models.Flowcell.create(consumable_id='TEST|TEST|TEST', consumable_type='TEST|TEST|TEST', path='TEST/TEST/TEST')
        tag, _ = models.Tag.get_or_create(name=tag)
        tag_j = models.TagJunction.create(flowcell=flow, tag=tag)
        self.assertIn(tag, flow.tags)

    def test_tag_failure(self):
        with self.assertRaises(Exception):
            tag = models.Tag.create(name='')

class TestFlowcell(TestBase):

    @given(sql_ints(), strat.text(), strat.text(), paths())
    def test_flowcell(self, pk, consumable_id, consumable_type, path):
        assert models.Flowcell.create(pk=pk,
                                      consumable_id=consumable_id,
                                      consumable_type=consumable_type,
                                      path=path)

class TestRun(TestBase):

    def setUp(self):
        super().setUp()
        self.flow = models.Flowcell.create(consumable_id='TEST',
                                           consumable_type='TEST',
                                           path='TEST/TEST')

    @given(pk=sql_ints(),
           name=strat.text(),
           library_id=strat.text(),
           alt_name=strat.text(),
           run_id=strat.text(),
           started=strat.datetimes().filter(lambda d: d < datetime.now()),
           ended=strat.datetimes().filter(lambda d: d > datetime.now()),
           path=paths(),
           basecalling_model=strat.one_of(*[strat.just(val) for val, _ in models.Run.basecallers]))
    def test_run(self, **kwargs):
        assert models.Run.create(flowcell=self.flow, **kwargs).run_duration

class TestQa(TestBase):

    @given(pk=sql_ints(),
           coverage=strat.floats().filter(lambda f: f > 0),
           quality=strat.floats().filter(lambda f: f > 0))
    def test_qa(self, **kwargs):
        assert models.Qa.create(**kwargs)

class TestJob(TestBase):

    @given(pk=sql_ints(),
           job_id=sql_ints(),
           status=strat.one_of(*[strat.just(val) for val, _ in models.Job.statuses]))
    def test_job(self, **kwargs):
        assert models.Job.create(**kwargs)

class TestSampleSheet(TestBase): #TODO

    @given(pk=sql_ints(),
           path=paths(),
           date=strat.datetimes(),
           sequencing_kit=strat.text())
    def test_samplesheet(self, **kwargs):
        assert models.SampleSheet.create(**kwargs)

    @skip('not implemented')
    def test_ss_from_csv(self):
        assert False

    @skip('not implemented')
    def test_ss_from_excel(self):
        assert False

class TestSample(TestBase): #TODO
    pass

class TestFile(TestBase): #TODO
    pass
