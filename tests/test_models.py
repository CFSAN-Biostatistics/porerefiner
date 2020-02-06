
from unittest import TestCase, skip
from unittest.mock import Mock, patch

from tests import paths, with_database, TestBase, sql_ints, samples, samplesheets, runs, jobs as _jobs

from porerefiner import models, jobs

from hypothesis import given, strategies as strat, example, seed, settings
#from hypothesis_fspaths import fspaths, _PathLike

from datetime import datetime
import pathlib
import sys



# safe_paths = lambda: fspaths().filter(lambda x: isinstance(x, str) or isinstance(x, _PathLike))
class TestJobDefinition(jobs.AbstractJob):
    pass


class TestModels(TestCase):

    @given(paths())
    @example(b'/path/pa')
    def test_path_field(self, path):
        try:
            pa = pathlib.Path(path)
        except TypeError:
            pa = pathlib.Path(str(path, encoding=sys.getfilesystemencoding()))
        fld = models.PathField()
        self.assertEqual(fld.python_value(fld.db_value(path)), pa)

    @given(job=_jobs())
    def test_job_field(self, job):
        fld = models.JobField()
        self.assertEqual(type(fld.python_value(fld.db_value(job))), type(job))

    def test_models_registered(self):
        self.assertEqual(len(models.REGISTRY), 8)

    @skip('broken')
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

# class TestFlowcell(TestCase):

#     @given(pk=sql_ints(),
#            consumable_id=strat.text(),
#            consumable_type=strat.text(),
#            path=paths())
#     @with_database
#     def test_flowcell(self, **kwargs):
#         assert models.Flowcell.create(**kwargs)

class TestRun(TestCase):

    @skip('broken')
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

    @settings(deadline=500)
    @given(run=runs(),
           job=_jobs())
    @with_database
    def test_job_spawn(self, run, job):
        # run.flowcell.save()
        run.save()
        self.assertIsNotNone(run.pk)
        jobb = run.spawn(job)
        #test that a deepcopy of the job state object was made
        self.assertIsNot(job, jobb.job_state)
        self.assertIsNot(job.submitter, jobb.job_state.submitter)

class TestQa(TestCase):

    @given(pk=sql_ints(),
           coverage=strat.floats().filter(lambda f: f > 0),
           quality=strat.floats().filter(lambda f: f > 0))
    @with_database
    def test_qa(self, **kwargs):
        assert models.Qa.create(**kwargs)



class TestJob(TestCase):

    @given(pk=sql_ints(),
           job_id=strat.text(),
           job_state=strat.just(TestJobDefinition(submitter=None)),
           status=strat.one_of(*[strat.just(val) for val, _ in models.Job.statuses]),
           datadir=paths())
    @with_database
    def test_job(self, **kwargs):
        assert models.Job.create(**kwargs)

    @skip('no test yet')
    def test_job_files(self):
        assert False

class TestSampleSheet(TestCase):

    @given(pk=sql_ints(),
           path=paths(),
           date=strat.datetimes(),
           sequencing_kit=strat.text())
    @with_database
    def test_samplesheet(self, **kwargs):
        assert models.SampleSheet.create(**kwargs)

    @skip('broken')
    @with_database
    def test_get_unused_sheets(self):
        self.flow = flow = models.Flowcell.create(consumable_id="TEST|TEST|TEST", consumable_type="TEST|TEST|TEST", path="TEST/TEST/TEST")
        self.run = models.Run.create(pk=100, library_id='x', name="TEST", flowcell=flow, path="TEST/TEST/TEST")
        self.assertFalse(models.SampleSheet.get_unused_sheets().count())
        models.SampleSheet.create(path="TEST")
        self.assertEqual(models.SampleSheet.get_unused_sheets().count(), 1)

    @skip('broken')
    @seed(5249283748837843916514315999694345497)
    @given(ss=samplesheets())
    @with_database
    def test_new_sheet_from_message(self, ss):
        flow = models.Flowcell.create(consumable_id="TEST|TEST|TEST", consumable_type="TEST|TEST|TEST", path="TEST/TEST/TEST")
        run = models.Run.create(pk=100, library_id='x', name="TEST", flowcell=flow, path="TEST/TEST/TEST")
        s = models.SampleSheet.new_sheet_from_message(ss, run)
        self.assertEqual(run.sample_sheet, s)

class TestSample(TestCase):

    @given(pk=sql_ints(),
           sample_id=strat.text(),
           accession=strat.text(),
           barcode_id=strat.text(),
           organism=strat.text(),
           extraction_kit=strat.text(),
           comment=strat.text(),
           user=strat.emails())
    @with_database
    def test_sample(self, **k):
        ss = models.SampleSheet.create(path=k['sample_id'])
        assert models.Sample.create(samplesheet=ss, **k)

class TestFile(TestCase):

    @given(pk=sql_ints(),
           path=paths(),
           checksum=strat.text(),
           last_modified=strat.datetimes(),
           exported=strat.booleans())
    @with_database
    def test_file(self, **k):
        assert models.File.create(**k)
