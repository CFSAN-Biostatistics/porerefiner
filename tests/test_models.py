
from unittest import TestCase, skip

from tests import paths, with_database, TestBase

from porerefiner import models

from hypothesis import given, strategies as strat
#from hypothesis_fspaths import fspaths, _PathLike

from datetime import datetime
import pathlib

# SQLite can't accept a 32-bit integer
sql_ints = lambda: strat.integers(min_value=-2**16, max_value=2**16)

# safe_paths = lambda: fspaths().filter(lambda x: isinstance(x, str) or isinstance(x, _PathLike))



class TestModels(TestCase):

    @given(paths())
    def test_path_field(self, path):
        #path = str(path)
        fld = models.PathField()
        self.assertEqual(fld.python_value(fld.db_value(path)), pathlib.Path(path))

    def test_models_registered(self):
        self.assertEqual(len(models.REGISTRY), 9)

    @given(tag=strat.text().filter(lambda x: x))
    @with_database
    def test_tags(self, tag):
        flow = models.Flowcell.create(consumable_id='TEST|TEST|TEST', consumable_type='TEST|TEST|TEST', path='TEST/TEST/TEST')
        tag, _ = models.Tag.get_or_create(name=tag)
        tag_j = models.TagJunction.create(flowcell=flow, tag=tag)
        self.assertIn(tag, flow.tags)

    @with_database
    def test_tag_failure(self):
        with self.assertRaises(Exception):
            tag = models.Tag.create(name='')

class TestFlowcell(TestCase):

    @given(pk=sql_ints(),
           consumable_id=strat.text(),
           consumable_type=strat.text(),
           path=paths())
    @with_database
    def test_flowcell(self, **kwargs):
        assert models.Flowcell.create(**kwargs)

class TestRun(TestCase):

    @given(pk=sql_ints(),
           name=strat.text(),
           library_id=strat.text(),
           alt_name=strat.text(),
           run_id=strat.text(),
           started=strat.datetimes().filter(lambda d: d < datetime.now()),
           ended=strat.datetimes().filter(lambda d: d > datetime.now()),
           path=paths(),
           basecalling_model=strat.one_of(*[strat.just(val) for val, _ in models.Run.basecallers]))
    @with_database
    def test_run(self, **kwargs):
        self.flow = models.Flowcell.create(consumable_id='TEST',
                                           consumable_type='TEST',
                                           path='TEST/TEST')
        assert models.Run.create(flowcell=self.flow, **kwargs).run_duration

class TestQa(TestCase):

    @given(pk=sql_ints(),
           coverage=strat.floats().filter(lambda f: f > 0),
           quality=strat.floats().filter(lambda f: f > 0))
    @with_database
    def test_qa(self, **kwargs):
        assert models.Qa.create(**kwargs)

class TestJob(TestCase):

    @given(pk=sql_ints(),
           job_id=sql_ints(),
           status=strat.one_of(*[strat.just(val) for val, _ in models.Job.statuses]))
    @with_database
    def test_job(self, **kwargs):
        assert models.Job.create(**kwargs)

class TestSampleSheet(TestCase): #TODO

    @given(pk=sql_ints(),
           path=paths(),
           date=strat.datetimes(),
           sequencing_kit=strat.text())
    @with_database
    def test_samplesheet(self, **kwargs):
        assert models.SampleSheet.create(**kwargs)

    @skip('not implemented')
    def test_ss_from_csv(self):
        assert False

    @skip('not implemented')
    def test_ss_from_excel(self):
        assert False

class TestSample(TestCase): #TODO
    pass

class TestFile(TestCase): #TODO
    pass
