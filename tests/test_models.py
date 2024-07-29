

from pytest import raises, mark


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
# class TestJobDefinition(jobs.AbstractJob):
#     pass

#@mark.skip("hangs")
@given(
    tag=names(),
    run=Model.Runs(),
    qa=Model.Qas(),
    duty=Model.Duties(),
    ss=Model.Samplesheets(),
    sam=Model.Samples(),
    fi=Model.Files())
def test_taggable_models_are_taggable(tag, run, qa, duty, ss, sam, fi):
    for obj in (run, qa, duty, ss, sam, fi):
        cls = type(obj)
        try:
            for attr in ("tags", "tag", "untag", "ttag", "unttag", "get_by_tags"):
                try:
                    assert hasattr(cls, attr), f"Expected taggable class {cls} to have been decorated with tag method {attr}"
                except Exception as e:
                    raise Exception(attr) from e
        except Exception as e:
            raise Exception(cls.__name__) from e


#@mark.skip("hangs")
@given(path=paths())
@example(b'/path/pa')
def test_path_field(path):
    try:
        pa = pathlib.Path(path)
    except TypeError:
        pa = pathlib.Path(str(path, encoding=sys.getfilesystemencoding()))
    fld = models.PathField()
    assert fld.python_value(fld.db_value(path)) == pa

# @given(job=_jobs())
# def test_job_field(self, job):
#     fld = models.JobField()
#     self.assertEqual(type(fld.python_value(fld.db_value(job))), type(job))

#@mark.skip("hangs")
def test_models_registered():
    assert len(models.REGISTRY) == 11

#@mark.skip("hangs")
@given(tag=strat.text().filter(lambda x: x))
def test_tags(db, tag):
    #peewee.logger.debug = lambda msg, *a, **k: peewee.logger.log(logging.ERROR, msg, *a, **k)
    # flow = models.SampleSheet.create()
    # tag, _ = models.Tag.get_or_create(name=tag)
    # tag_j = models.TagJunction.create(samplesheet=flow, tag=tag)
    # self.assertIn(tag, flow.tags)
    ut = models.Run.create(name="TEST", path="TEST")
    tag = ut.tag("TEST")
    assert tag in ut.tags
    ut.untag(tag.name)
    ttag = ut.ttag("TEST", "TEST", "TEST")
    assert ttag in ut.tags
    ut.unttag(ttag.namespace, ttag.name)
    assert tag not in ut.tags
    assert ttag not in ut.tags
    #peewee.logger.debug = lambda msg, *a, **k: peewee.logger.log(logging.DEBUG - 5, msg, *a, **k)

#@mark.skip("hangs")
def test_extended_tag_interfaces(db):
    ut = models.Run.create(name="TEST", path="TEST")
    ttag = ut.ttag("TEST", "TEST", "TEST")
    assert ut.tags["TEST"]['TEST'] == "TEST"
    assert ut.tags.TEST.TEST == "TEST"


#@mark.skip("hangs")
def test_tag_failure(db):
    with raises(Exception):
        tag = models.Tag.create(name='')

# class TestFlowcell(TestCase):

#     @given(pk=sql_ints(),
#            consumable_id=strat.text(),
#            consumable_type=strat.text(),
#            path=paths())
#     @with_database
#     def test_flowcell(self, **kwargs):
#         assert models.Flowcell.create(**kwargs)

# class TestRun(TestCase):

# @skip('broken')
# @given(pk=sql_ints(),
#         name=strat.text(),
#         library_id=strat.text(),
#         alt_name=strat.text(),
#         run_id=strat.text(),
#         started=strat.datetimes().filter(lambda d: d < datetime.now()),
#         ended=strat.datetimes().filter(lambda d: d > datetime.now()),
#         path=paths(),
#         basecalling_model=strat.one_of(*[strat.just(val) for val, _ in models.Run.basecallers]))
# @with_database
# def test_run(**kwargs):
#     self.flow = models.Flowcell.create(consumable_id='TEST',
#                                         consumable_type='TEST',
#                                         path='TEST/TEST')
#     assert models.Run.create(flowcell=self.flow, **kwargs).run_duration

#@mark.skip("hangs")
#@settings(deadline=None, suppress_health_check=(HealthCheck.all()))
@given(run=Model.Runs(),
        job=_jobs())
def test_job_spawn(db, run, job):
    # run.flowcell.save()
    run.save()
    assert run.id is not None
    jobb = run.spawn(job)
    assert job is jobb.job_state

#@mark.skip("hangs")
@given(pk=sql_ints(),
        coverage=strat.floats().filter(lambda f: f > 0),
        quality=strat.floats().filter(lambda f: f > 0))
def test_qa(db, **kwargs):
    assert models.Qa.create(**kwargs)


#@mark.skip("hangs")
@given(job=Model.Duties())
def test_job(db, job):
    assert job.save()

#@mark.skip("hangs")
@given(job=Model.Duties(),
        path=paths(pathlib_only=True))
def test_job_files(db, job, path):
    job.save()
    # file = models.File(path=path)
    # file.save()
    file = models.File.create(path=path)
    job.files.add(file)
    job.save()
    assert file in job.files

#@mark.skip("hangs")
@given(pk=sql_ints(),
        path=paths(),
        date=strat.datetimes(),
        sequencing_kit=strat.text())
def test_samplesheet(db, **kwargs):
    assert models.SampleSheet.create(**kwargs)

#@mark.skip("hangs")
def test_get_unused_sheets(db):
    # self.flow = flow = models.Flowcell.create(consumable_id="TEST|TEST|TEST", consumable_type="TEST|TEST|TEST", path="TEST/TEST/TEST")
    run = models.Run.create(pk=100, library_id='x', name="TEST", path="TEST/TEST/TEST")
    assert models.SampleSheet.get_unused_sheets().count() == 0
    models.SampleSheet.create(path="TEST")
    assert models.SampleSheet.get_unused_sheets().count() == 1

#@mark.skip("hangs")
@given(ss=Message.Samplesheets())
def test_new_sheet_from_message(db, ss):
    # flow = models.Flowcell.create(consumable_id="TEST|TEST|TEST", consumable_type="TEST|TEST|TEST", path="TEST/TEST/TEST")
    run = models.Run.create(pk=100, library_id='x', name="TEST", path="TEST/TEST/TEST")
    s = models.SampleSheet.new_sheet_from_message(ss, run)
    assert run.sample_sheet == s


#@mark.skip("hangs")
@given(pk=sql_ints(),
        sample_id=strat.text(),
        accession=strat.text(),
        barcode_id=strat.text(),
        organism=strat.text(),
        extraction_kit=strat.text(),
        comment=strat.text(),
        user=strat.emails())
def test_sample(db, **k):
    ss = models.SampleSheet.create(path=k['sample_id'])
    assert models.Sample.create(samplesheet=ss, **k)


#@mark.skip("hangs")
@given(pk=sql_ints(),
        path=paths(),
        checksum=strat.text(),
        last_modified=strat.datetimes(),
        exported=strat.booleans())
def test_file(db, **k):
    assert models.File.create(**k)

#@mark.skip("hangs")
@given(pk=sql_ints(),
        path=paths(),
        checksum=strat.text(),
        last_modified=strat.datetimes(),
        exported=strat.booleans(),
        job=Model.Duties())
def test_job_spawn(db, job, **k):
    fi = models.File.create(**k)
    assert fi.spawn(job)


    


"Tests for a bunch of tag-related bugs"


#@mark.skip("hangs")
def test_lookup_by_tags(db):
    from porerefiner.models import Run, Tag, TagJunction, TripleTag, TTagJunction
    tags = ("TEST", "another tag")
    run = Run.create(name="TEST", path="/dev/null")
    run.tag(tags[0])
    assert len(Run.get_by_tags(*tags)) == 1
    run.ttag(namespace="TEST", name="TEST", value=tags[0])
    assert len(Run.get_by_tags(*tags)) == 1

#@mark.skip("hangs")
@given(
    tags=strat.lists(names(), min_size=1, unique=True),
    run=Model.Runs())
def test_tags_dont_bump_each_other(db, tags, run):
    run.save()
    for tag in tags:
        run.tag(tag)
    assert len(list(run.tags)) == len(tags)

#@mark.skip("hangs")
@mark.asyncio
@settings(deadline=None)
@given(tag=names(), run=Model.Runs())
async def test_tags_arent_deleted_on_run_end(db, tag, run):
    run.save()
    ta = run.tag(tag)
    tta = run.ttag(tag, tag, tag)
    await fsevents.end_run(run)
    fin = models.Tag.get(name="finished")
    assert ta in run.tags
    assert fin in run.tags
    assert tta in run.tags


#@mark.skip("hangs")
@mark.asyncio
@given(
    tag=names(),
    file_event=file_events(),
    run=Model.Runs()
)
async def test_tags_arent_deleted_on_file_deletion(db, tag, file_event, run):
    file, event = file_event
    assert file.path == event.src_path
    file.save()
    models.File.get(file.id)
    file.tag(tag)
    run.save()
    tag = run.tag(tag)
    assert len(list(run.tags)) == 1
    assert len(list(file.tags)) == 1
    await Handler(event.src_path.parts[0]).on_deleted(event)
    assert models.File.get_or_none(models.File.path==event.src_path) is None # check file record is gone
    assert len(list(run.tags)) == 1
    assert tag in run.tags