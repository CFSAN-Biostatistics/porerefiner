import peewee
from peewee import *
#from porerefiner.config import config

import asyncio
import datetime
import logging
import pathlib
import pickle
import namesgenerator
import sys
import tempfile

from copy import copy, deepcopy
from itertools import chain

logging.addLevelName(logging.DEBUG - 5, 'TRACE')

#slightly demote the Peewee debug logging
peewee.logger.debug = lambda msg, *a, **k: peewee.logger.log(logging.DEBUG - 5, msg, *a, **k)


_db = SqliteDatabase(None)

class BaseModel(Model):

    class Meta:
        database = _db

class PorerefinerModel(BaseModel):
    "Abstract base class for PoreRefiner models"

    statuses = [('READY', 'Ready to Run'),
                ('QUEUED', 'Scheduled to Run'),
                ('RUNNING', 'Running'),
                ('STOPPING', 'Stopping'),
                ('DONE', 'Ended'),
                ('FAILED', 'Ended with Failure')]

    @property
    def tags(self):
        # query = Tag.select().join(TagJunction).join(Tag)
        # return [tag_j.tag for tag_j in self.tag_junctions]
        return (Tag.select()
                   .join(TagJunction)
                   .join(type(self))
                   .where(type(self).pk == self.pk))

    # def tag(self, *tags):
    #     for tag in tags:
    #         Tag.get_or_create(name=tag)



class Tag(BaseModel):
    "A tag is an informal annotation"

    name = CharField(null=False, constraints=[Check("name != '' ")])

    def __str__(self):
        return self.name

class PathField(Field):

    field_type = 'varchar'

    def db_value(self, value):
        if hasattr(value, '__fspath__'):
            value = str(value)
        if isinstance(value, bytes):
            value = str(value.decode(sys.getfilesystemencoding(), 'surrogateescape'))
        return value

    def python_value(self, value):
        if value:
            return pathlib.Path(value)
        return None


# class JobField(Field):

#     field_type = 'blob'

#     def db_value(self, value):
#         from porerefiner.jobs import AbstractJob
#         if not isinstance(value, AbstractJob):
#             raise ValueError(f"value of type {type(value)} can't be stored in this field.")
#         return pickle.dumps(value)

#     def python_value(self, value):
#         return pickle.loads(value)

def StatusField(*args, default=PorerefinerModel.statuses[0][0], **kwargs):
    return CharField(*args, choices=PorerefinerModel.statuses, default=default, **kwargs)


def create_readable_name():
    "Docker-style random name from namesgenerator"
    return namesgenerator.get_random_name()

# class Flowcell(PorerefinerModel):
#     "A flowcell is the disposable part of the sequencer"

#     pk = AutoField()

#     consumable_id = CharField(null=False)
#     consumable_name = CharField(null=False)
#     consumable_type = CharField(null=True)
#     path = PathField(index=True)

class Run(PorerefinerModel):
    "A run is an annotated collection of files being produced"

    basecallers = [('DNA', 'DNA Basecaller'),
                   ('RNA', 'RNA Basecaller')]

    pk = AutoField()

    # flowcell = ForeignKeyField(Flowcell, backref='runs')
    flowcell = CharField(null=True)
    _sample_sheet = DeferredForeignKey('SampleSheet', null=True, backref='runs')

    name = CharField()
    library_id = CharField(null=True)
    alt_name = CharField(default = create_readable_name)
    run_id = CharField(null=True)
    started = DateTimeField(default = datetime.datetime.now)
    ended = DateTimeField(null=True, default=None)
    status = StatusField(default='RUNNING')
    path = PathField(index=True)
    basecalling_model = CharField(default='DNA', choices=basecallers, null=True)

    def __str__(self):
        return f"{self.pk} {self.alt_name} ({self.path}) ({dict(self.statuses)[self.status]})"

    @property
    def all_files(self):
        return chain(self.files, chain(*(sample.files for sample in self.samples)))

    @property
    def jobs(self):
        return chain(*(file.jobs for file in self.all_files))

    @property
    def run_duration(self):
        if self.ended:
            return self.ended - self.started

    @property
    def sample_sheet(self):
        return self._sample_sheet or SampleSheet()

    @sample_sheet.setter
    def sample_sheet(self, ss):
        self._sample_sheet = ss

    @property
    def samples(self):
        return self.sample_sheet.samples

    @classmethod
    def get_unannotated_runs(cls):
        return cls.select().where(cls._sample_sheet.is_null(), cls.status=='RUNNING')

    def tag(self, tag):
        ta, _ = Tag.get_or_create(name=tag)
        tj, _ = TagJunction.get_or_create(tag=ta, run=self)
        return ta

    def untag(self, tag):
        ta = Tag.get_or_none(name=tag)
        if ta:
            TagJunction.delete().where(TagJunction.run==self, TagJunction.tag==ta).execute()

    @property
    def tags(self):
        return (Tag.select()
                   .join(TagJunction)
                   .where(TagJunction.run == self))

    def spawn(self, job_config):
        job = Job.create(status='READY', job_class=job_config.__class__.__name__, datadir=pathlib.Path(tempfile.mkdtemp()), run=self)
        # JobRunJunction.create(job=job, run=self)
        # for file in self.files:
        #     JobFileJunction.create(job=job, file=file)
        return job

# class JobRunJunction(BaseModel):
#     pk = AutoField()
#     job = DeferredForeignKey('Job', backref='jobs')
#     run = ForeignKeyField(Run, backref='runs')


class Qa(PorerefinerModel):
    "A QA is a set of quality-control analysis metrics"

    pk = AutoField()
    coverage = FloatField()
    quality = FloatField()


class Job(PorerefinerModel):
    "A job is a scheduled HPC job, pre or post submission"
    pk = AutoField()
    job_id = CharField(null=True)
    # job_state = JobField(null=True)
    job_class = TextField(null=False)
    status = StatusField(default='QUEUED')
    datadir = PathField(null=False)
    outputdir = PathField(null=True)
    run = ForeignKeyField(Run, null=True, backref='jobs')
    file = DeferredForeignKey('File', backref='_jobs_with_this_file_as_primary', null=True)


    def __str__(self):
        return f"{self.pk} ({self.job_class}) ({dict(self.statuses)[self.status]})"

    # @property
    # def files(self):
    #     return (File.select()
    #                 .join(JobFileJunction)
    #                 .join(Job)
    #                 .where(Job.pk == self.pk))

    @property
    def job_state(self):
        import porerefiner.jobs
        return porerefiner.jobs.CONFIGURED_JOB_REGISTRY[self.job_class]

    def tag(self, tag):
        ta, _ = Tag.get_or_create(name=tag)
        tj, _ = TagJunction.get_or_create(tag=ta, job=self)
        return ta

# class JobFileJunction(BaseModel):
#     pk = AutoField()
#     job = ForeignKeyField(Job, backref='jobs')
#     file = DeferredForeignKey('File', backref='files')

class SampleSheet(PorerefinerModel):
    "A samplesheet is a particular file, eventually attached to a run"

    BARCODES = [('SQK-16S024','16S Barcoding Kit 1-24 SQK-16S024'),
                ('EXP-NBD104','Native Barcoding Expansion 1-12 EXP-NBD104'),
                ('EXP-NBD114','Native Barcoding Expansion 13-24 EXP-NBD114'),
                ('EXP-NBD104+EXP-NBD114','Native Barcoding Expansions 1-12 and 13-24 EXP-NBD104+EXP-NBD114'),
                ('SQK-LSK109', 'Ligation Sequencing Kit, no barcodes SQK-LSK109'),
                # ('EXP-NBD103',''),
                # ('EXP-PBC001',''),
                # ('EXP-PBC096',''),
                # ('SQK-LWB001',''),
                # ('SQK-PBK004',''),
                # ('SQK-PCB109',''),
                # ('SQK-RAB201',''),
                # ('SQK-RAB204',''),
                # ('SQK-RBK001',''),
                # ('VSK-VMK001',''),
                # ('VSK-VMK002',''),
                # ('SQK-RLB001',''),
                ('SQK-RBK004','Rapid Barcoding Kit SQK-RBK004'),
                ('SQK-RPB004','Rapid PCR Barcoding Kit SQK-RPB004')]


    pk = AutoField()
    # path = PathField(index=True)
    # run = ForeignKeyField(Run, backref='_sample_sheet', unique=True, null=True)
    date = DateField(null=True, default=datetime.datetime.now())
    sequencing_kit = CharField(null=True)
    barcoding_kit = CharField(null=True, choices=BARCODES)
    library_id = CharField(null=True)

    @property
    def barcode_kit_barcodes(self):
        return {} #TODO

    @classmethod
    def get_unused_sheets(cls):
        return (cls.select()
                   .join(Run, JOIN.LEFT_OUTER)
                   .switch()
                   .where(Run.pk.is_null()))

    @classmethod
    def new_sheet_from_message(cls, sheet, run=None, log=logging.getLogger('porerefiner.models')):
        ss = cls.create(date=sheet.date.ToDatetime(),
                        barcoding_kit=sheet.sequencing_kit,
                        library_id=sheet.library_id)
        for sample in sheet.samples:
            Sample.create(sample_id=sample.sample_id,
                          accession=sample.accession,
                          barcode_id=sample.barcode_id,
                          organism=sample.organism,
                          extraction_kit=sample.extraction_kit,
                          comment=sample.comment,
                          user=sample.user,
                          samplesheet=ss)
        if run:
            run.sample_sheet = ss
            run.save()
        return ss

class Sample(PorerefinerModel):
    "A sample is an entry originally from a sample sheet"



    pk = AutoField()
    sample_id = CharField(null=False)
    accession = CharField(default="")
    barcode_id = CharField(null=False)
    #barcode_seq = CharField() #maybe set this when we load a sheet
    organism = CharField(default="")
    extraction_kit = CharField(default="")
    comment = CharField(default="")
    user = CharField(null=True)




    samplesheet = ForeignKeyField(SampleSheet, backref='samples')

    @property
    def barcode_seq(self):
        return self.samplesheet.barcode_kit_barcodes.get(self.barcode_id, "")

    @property
    def tags(self):
        return (Tag.select()
                   .join(TagJunction)
                   .where(TagJunction.sample == self))

    def tag(self, tag):
        ta, _ = Tag.get_or_create(name=tag)
        tj, _ = TagJunction.get_or_create(tag=ta, sample=self)
        return ta



class File(PorerefinerModel):
    "A file is a path on the filesystem"
    pk = AutoField()
    run = ForeignKeyField(Run, backref='files', null=True)
    sample = ForeignKeyField(Sample, backref='files', null=True)
    path = PathField(index=True, unique=True)
    checksum = CharField(index=True, null=True)
    last_modified = DateTimeField(default=datetime.datetime.now)
    exported = IntegerField(default=0)
    _jobs = ManyToManyField(Job, backref='files')

    @property
    def name(self):
        return self.path.name

    # @property
    # def jobs(self):
    #     return (Job.select()
    #                .join(JobFileJunction)
    #                .join(File)
    #                .where(File.pk == self.pk))

    def spawn(self, job_config):
        job = Job.create(status='READY', job_class=job_config.__class__.__name__, datadir=pathlib.Path(tempfile.mkdtemp()), file=self)
        self._jobs.add(job)
        return job

    def tag(self, tag):
        ta, _ = Tag.get_or_create(name=tag)
        tj, _ = TagJunction.get_or_create(tag=ta, file=self)
        return ta

    @property
    def jobs(self):
        yield from self._jobs_with_this_file_as_primary
        yield from self._jobs


class TagJunction(BaseModel):
    tag = ForeignKeyField(Tag, backref='junctions')
    # flowcell = ForeignKeyField(Flowcell, null=True, backref='tag_junctions')
    run = ForeignKeyField(Run, null=True, backref='tag_junctions')
    qa = ForeignKeyField(Qa, null=True, backref='tag_junctions')
    job = ForeignKeyField(Job, null=True, backref='tag_junctions')
    samplesheet = ForeignKeyField(SampleSheet, null=True, backref='tag_junctions')
    sample = ForeignKeyField(Sample, null=True, backref='tag_junctions')
    file = ForeignKeyField(File, null=True, backref='tag_junctions')

    # @classmethod
    # def relate(cls, target, tag):
    #     targ_cls = type(target)
    #     for field, ref_cls, _ in cls._meta.model_graph(backrefs=False, depth_first=False):
    #         if ref_cls is targ_cls:
    #             return cls.create

JobFileJunction = File._jobs.get_through_model()


REGISTRY = [Tag, Run, Qa, Job, SampleSheet, Sample, File, TagJunction, JobFileJunction]
