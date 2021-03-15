
from unittest import TestCase, skip
from unittest.mock import Mock, patch

from tests import _run
from tests import *

_jobs = jobs

from porerefiner import models, jobs, fsevents
from porerefiner.fsevents import PoreRefinerFSEventHandler as Handler

from hypothesis import given, strategies as strat, example, seed, settings, HealthCheck
#from hypothesis_fspaths import fspaths, _PathLike

from datetime import datetime
import pathlib
import sys



# safe_paths = lambda: fspaths().filter(lambda x: isinstance(x, str) or isinstance(x, _PathLike))
class TestJobDefinition(jobs.AbstractJob):
    pass

class TestTaggableModels(TestCase):

    @given(
        tag=names(),
        run=Model.Runs(),
        qa=Model.Qas(),
        duty=Model.Duties(),
        ss=Model.Samplesheets(),
        sam=Model.Samples(),
        fi=Model.Files())
    @with_database
    def test_taggable_models_are_taggable(self, tag, run, qa, duty, ss, sam, fi):
        for obj in (run, qa, duty, ss, sam, fi):
            cls = type(obj)
            try:
                for attr in ("tags", "tag", "untag", "ttag", "unttag", "get_by_tags"):
                    try:
                        self.assertTrue(hasattr(cls, attr))
                    except Exception as e:
                        raise Exception(attr) from e
            except Exception as e:
                raise Exception(cls.__name__) from e



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

    # @given(job=_jobs())
    # def test_job_field(self, job):
    #     fld = models.JobField()
    #     self.assertEqual(type(fld.python_value(fld.db_value(job))), type(job))

    def test_models_registered(self):
        self.assertEqual(len(models.REGISTRY), 11)

    # @skip('broken')
    @given(tag=strat.text().filter(lambda x: x))
    @with_database
    def test_tags(self, tag):
        import peewee
        import logging
        #peewee.logger.debug = lambda msg, *a, **k: peewee.logger.log(logging.ERROR, msg, *a, **k)
        # flow = models.SampleSheet.create()
        # tag, _ = models.Tag.get_or_create(name=tag)
        # tag_j = models.TagJunction.create(samplesheet=flow, tag=tag)
        # self.assertIn(tag, flow.tags)
        ut = models.Run.create(name="TEST", path="TEST")
        tag = ut.tag("TEST")
        self.assertIn(tag, ut.tags)
        ut.untag(tag.name)
        ttag = ut.ttag("TEST", "TEST", "TEST")
        self.assertIn(ttag, ut.tags)
        ut.unttag(ttag.namespace, ttag.name)
        self.assertNotIn(tag, ut.tags)
        self.assertNotIn(ttag, ut.tags)
        #peewee.logger.debug = lambda msg, *a, **k: peewee.logger.log(logging.DEBUG - 5, msg, *a, **k)



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

    @settings(deadline=None, suppress_health_check=(HealthCheck.all()))
    @given(run=Model.Runs(),
           job=_jobs())
    @with_database
    def test_job_spawn(self, run, job):
        # run.flowcell.save()
        run.save()
        self.assertIsNotNone(run.pk)
        jobb = run.spawn(job)
        self.assertIs(job, jobb.job_state)

class TestQa(TestCase):

    @given(pk=sql_ints(),
           coverage=strat.floats().filter(lambda f: f > 0),
           quality=strat.floats().filter(lambda f: f > 0))
    @with_database
    def test_qa(self, **kwargs):
        assert models.Qa.create(**kwargs)



class TestJob(TestCase):

    @given(job=Model.Duties())
    @with_database
    def test_job(self, job):
        assert job.save()

    # @skip('no test yet')
    @given(job=Model.Duties(),
           path=paths(pathlib_only=True))
    @with_database
    def test_job_files(self, job, path):
        job.save()
        # file = models.File(path=path)
        # file.save()
        file = models.File.create(path=path)
        job.files.add(file)
        job.save()
        self.assertIn(file, job.files)

class TestSampleSheet(TestCase):

    @given(pk=sql_ints(),
           path=paths(),
           date=strat.datetimes(),
           sequencing_kit=strat.text())
    @with_database
    def test_samplesheet(self, **kwargs):
        assert models.SampleSheet.create(**kwargs)

    # @skip('broken')
    @with_database
    def test_get_unused_sheets(self):
        # self.flow = flow = models.Flowcell.create(consumable_id="TEST|TEST|TEST", consumable_type="TEST|TEST|TEST", path="TEST/TEST/TEST")
        self.run = models.Run.create(pk=100, library_id='x', name="TEST", path="TEST/TEST/TEST")
        self.assertFalse(models.SampleSheet.get_unused_sheets().count())
        models.SampleSheet.create(path="TEST")
        self.assertEqual(models.SampleSheet.get_unused_sheets().count(), 1)

    # @skip('broken')
    @given(ss=Message.Samplesheets())
    @with_database
    def test_new_sheet_from_message(self, ss):
        # flow = models.Flowcell.create(consumable_id="TEST|TEST|TEST", consumable_type="TEST|TEST|TEST", path="TEST/TEST/TEST")
        run = models.Run.create(pk=100, library_id='x', name="TEST", path="TEST/TEST/TEST")
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

    @given(pk=sql_ints(),
           path=paths(),
           checksum=strat.text(),
           last_modified=strat.datetimes(),
           exported=strat.booleans(),
           job=Model.Duties())
    @with_database
    def test_job_spawn(self, job, **k):
        fi = models.File.create(**k)
        assert fi.spawn(job)


    
class TestTags(TestBase):

    "Tests for a bunch of tag-related bugs"

    @skip("broken")
    def test_complex_query(self):
        from porerefiner.models import Run, Tag, TagJunction, TripleTag, TTagJunction
        tags = ("TEST", "another tag")
        self.assertFalse(Run.select().join(TagJunction).join(Tag).where(Tag.name << tags).switch(Run).join(TTagJunction).join(TripleTag).where(TripleTag.value << tags))

    @skip("old approach")
    def test_tagging_assumptions(self):
        from porerefiner.models import Run, Tag, TagJunction, TripleTag, TTagJunction
        tags = ("TEST", "another tag")
        run = Run.create(name="TEST", path="/dev/null")
        self.assertEqual(len(Run.select().join(TagJunction).join(Tag).where(Tag.name << tags)), 0) # test simple query no tags
        run.tag(tags[0])
        self.assertEqual(len(Run.select().join(TagJunction).join(Tag).where(Tag.name << tags)), 1) # test simple query, one tag
        self.assertEqual(len(Run.select().join(TagJunction).join(Tag).where(Tag.name << tags).switch(Run).join(TTagJunction).join(TripleTag).where(TripleTag.value << tags)), 1) #test complicated query with simple tag
        run.ttag(namespace="TEST", name="TEST", value=tags[0])
        self.assertEqual(len(Run.select().join(TagJunction).join(Tag).where(Tag.name << tags).switch(Run).join(TTagJunction).join(TripleTag).where(TripleTag.value << tags)), 1) # complicated query with two tags but one result

    def test_lookup_by_tags(self):
        from porerefiner.models import Run, Tag, TagJunction, TripleTag, TTagJunction
        tags = ("TEST", "another tag")
        run = Run.create(name="TEST", path="/dev/null")
        run.tag(tags[0])
        self.assertEqual(len(Run.get_by_tags(*tags)), 1)
        run.ttag(namespace="TEST", name="TEST", value=tags[0])
        self.assertEqual(len(Run.get_by_tags(*tags)), 1)

    @given(
        tags=strat.lists(names(), min_size=1, unique=True),
        run=Model.Runs())
    def test_tags_dont_bump_each_other(self, tags, run):
        run.save()
        for tag in tags:
            run.tag(tag)
        self.assertEqual(len(list(run.tags)), len(tags))

    # @skip("")
    @settings(deadline=None)
    @given(tag=names(), run=Model.Runs())
    def test_tags_arent_deleted_on_run_end(self, tag, run):
        run.save()
        ta = run.tag(tag)
        tta = run.ttag(tag, tag, tag)
        _run(fsevents.end_run(run))
        fin = models.Tag.get(name="finished")
        self.assertIn(ta, run.tags)
        self.assertIn(fin, run.tags)
        self.assertIn(tta, run.tags)

    # @skip("")
    @given(
        tag=names(),
        file_event=file_events(),
        run=Model.Runs()
    )
    def test_tags_arent_deleted_on_file_deletion(self, tag, file_event, run):
        file, event = file_event
        assert file.path == event.src_path
        file.save()
        models.File.get(file.id)
        file.tag(tag)
        run.save()
        tag = run.tag(tag)
        self.assertEqual(len(list(run.tags)), 1)
        self.assertEqual(len(list(file.tags)), 1)
        _run(Handler(event.src_path.parts[0]).on_deleted(event))
        self.assertFalse(models.File.get_or_none(models.File.path==event.src_path)) # check file record is gone
        self.assertEqual(len(list(run.tags)), 1)
        self.assertIn(tag, run.tags)