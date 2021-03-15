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




class Tag(BaseModel):
    "A tag is an informal annotation"

    name = CharField(null=False, constraints=[Check("name != '' ")])

    def __str__(self):
        return self.name

class TripleTag(BaseModel):
    "A triple tag extends tag with a namespace and value"

    namespace = CharField(null=False, 
                          constraints=[Check("namespace != '' "),], 
                          default="Porerefiner")

    name = CharField(null=False, constraints=[Check("name != '' "),])

    value = BareField(null=False)

    def __str__(self):
        return f"{self.namespace}:{self.name}={self.value}"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.namespace}, {self.name}, {self.value})"

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


def StatusField(*args, default=PorerefinerModel.statuses[0][0], **kwargs):
    return CharField(*args, choices=PorerefinerModel.statuses, default=default, **kwargs)


def create_readable_name():
    "Docker-style random name from namesgenerator"
    return namesgenerator.get_random_name()


def taggable(cls):
    "Class decorator to insert the tag creation and deletion methods"
    def make_closures(clsname):

        @property
        def tags(self):
            # query = Tag.select().join(TagJunction).join(Tag)
            # return [tag_j.tag for tag_j in self.tag_junctions]
            return chain(Tag.select()
                            .join(TagJunction)
                            .join(type(self))
                            .where(type(self).pk == self.pk),
                        TripleTag.select()
                            .join(TTagJunction)
                            .join(type(self))
                            .where(type(self).pk == self.pk))

        def tag(self, tag):
            ta, _ = Tag.get_or_create(name=tag)
            _, _ = TagJunction.get_or_create(tag=ta, **{clsname:self})
            return ta

        def untag(self, tag):
            ta = Tag.get_or_none(name=tag)
            if ta:
                TagJunction.delete().where(getattr(TagJunction, clsname)==self, TagJunction.tag==ta).execute()

        def ttag(self, namespace, name, value):
            ta, _ = TripleTag.get_or_create(namespace=namespace, name=name, value=value)
            _, _ = TTagJunction.get_or_create(tag=ta, **{clsname:self})
            return ta

        def unttag(self, namespace, name):
            ta = TripleTag.get_or_none(namespace=namespace, name=name)
            if ta:
                TTagJunction.delete().where(getattr(TTagJunction, clsname)==self, TTagJunction.tag==ta).execute()
        
        @classmethod
        def get_by_tags(self, *tags):
            return self.select().join(TagJunction).join(Tag).where(Tag.name << tags) | self.select().join(TTagJunction).join(TripleTag).where(TripleTag.value << tags)

        return tags, tag, untag, ttag, unttag, get_by_tags

    cls.tags, cls.tag, cls.untag, cls.ttag, cls.unttag, cls.get_by_tags = make_closures(cls.__name__.lower())
    return cls

@taggable
class Run(PorerefinerModel):
    "A run is an annotated collection of files being produced"

    basecallers = [('DNA', 'DNA Basecaller'),
                   ('RNA', 'RNA Basecaller')]

    pk = AutoField()

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


    def spawn(self, job_config):
        return Duty.create(status='READY', job_class=job_config.__class__.__name__, datadir=pathlib.Path(tempfile.mkdtemp()), run=self)


@taggable
class Qa(PorerefinerModel):
    "A QA is a set of quality-control analysis metrics"

    pk = AutoField()
    coverage = FloatField()
    quality = FloatField()

    def __str__(self):
        return f"QA: {self.coverage:02} / {self.quality:02}"

@taggable
class Duty(PorerefinerModel):
    "A job is a scheduled HPC job, pre or post submission"
    pk = AutoField()
    job_id = CharField(null=True)
    job_class = TextField(null=False)
    status = StatusField(default='QUEUED')
    datadir = PathField(null=False)
    outputdir = PathField(null=True)
    run = ForeignKeyField(Run, null=True, backref='duties')
    file = DeferredForeignKey('File', backref='_duties_with_this_file_as_primary', null=True)
    attempts = IntegerField(default=0)


    def __str__(self):
        return f"{self.pk} ({self.job_class} for {self.purpose}) ({dict(self.statuses)[self.status]})"


    @property
    def purpose(self):
        if self.run:
            return self.run.alt_name
        if self.file:
            return self.file.path

    @property
    def job_state(self):
        import porerefiner.jobs
        return porerefiner.jobs.CONFIGURED_JOB_REGISTRY[self.job_class]


@taggable
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
    date = DateField(null=True, default=datetime.datetime.now())
    sequencing_kit = CharField(null=True)
    barcoding_kit = CharField(null=True, choices=BARCODES)
    library_id = CharField(null=True)
    path = PathField(null=True)

    def __str__(self):
        return f"SampleSheet: {self.path} | {len(self.samples)} samples."

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
    def new_sheet_from_message(cls, sheet, run=None, log=logging.getLogger('porerefiner.models'), sample_accession_prefix=None):
        for ss in cls.get_unused_sheets():
            # clear out any previously unassigned sample sheets
            # there should only ever be one unassigned sheet
            for sam in ss.samples:
                sam.delete_instance()
            ss.delete_instance
        ss = cls.create(date=sheet.date.ToDatetime(),
                        barcoding_kit=sheet.sequencing_kit,
                        library_id=sheet.library_id)
        for tag in sheet.tags:
            ss.tag(tag)
        for ttag in sheet.trip_tags:
            ss.ttag(ttag.namespace, ttag.name, ttag.value)
        if not sample_accession_prefix:
            sample_accession_prefix = "SAM"
            if run:
                sample_accession_prefix = run.alt_name
        for num, sample in enumerate(sheet.samples):
            s = Sample.create(sample_id=sample.sample_id,
                          accession=sample.accession or f"{sample_accession_prefix}_{num:06}",
                          barcode_id=sample.barcode_id,
                          organism=sample.organism,
                          extraction_kit=sample.extraction_kit,
                          comment=sample.comment,
                          user=sample.user,
                          samplesheet=ss)
            for ttag in sample.trip_tags:
                s.ttag(ttag.namespace, ttag.name, ttag.value)
        if run:
            run.sample_sheet = ss
            run.save()
        return ss

@taggable
class Sample(PorerefinerModel):
    "A sample is an entry originally from a sample sheet"



    pk = AutoField()
    sample_id = CharField(null=False)
    accession = CharField(default="")
    barcode_id = CharField(null=False)
    organism = CharField(default="")
    extraction_kit = CharField(default="")
    comment = CharField(default="")
    user = CharField(null=True)




    samplesheet = ForeignKeyField(SampleSheet, backref='samples')

    @property
    def barcode_seq(self):
        return self.samplesheet.barcode_kit_barcodes.get(self.barcode_id, "")


@taggable
class File(PorerefinerModel):
    "A file is a path on the filesystem"


    pk = AutoField()
    run = ForeignKeyField(Run, backref='files', null=True)
    sample = ForeignKeyField(Sample, backref='files', null=True)
    path = PathField(index=True, unique=True)
    checksum = CharField(index=True, null=True)
    last_modified = DateTimeField(default=datetime.datetime.now)
    exported = IntegerField(default=0)
    _duties = ManyToManyField(Duty, backref='files')

    @property
    def name(self):
        return self.path.name

    def spawn(self, job_config):
        job = Duty.create(status='READY', job_class=job_config.__class__.__name__, datadir=pathlib.Path(tempfile.mkdtemp()), file=self)
        self._duties.add(job)
        return job


    @property
    def duties(self):
        yield from self._duties_with_this_file_as_primary
        yield from self._duties


class TagJunction(BaseModel):
    tag = ForeignKeyField(Tag, backref='junctions')
    run = ForeignKeyField(Run, null=True, backref='tag_junctions')
    qa = ForeignKeyField(Qa, null=True, backref='tag_junctions')
    duty = ForeignKeyField(Duty, null=True, backref='tag_junctions')
    samplesheet = ForeignKeyField(SampleSheet, null=True, backref='tag_junctions')
    sample = ForeignKeyField(Sample, null=True, backref='tag_junctions')
    file = ForeignKeyField(File, null=True, backref='tag_junctions')


class TTagJunction(BaseModel):
    tag = ForeignKeyField(TripleTag, backref='junctions')
    run = ForeignKeyField(Run, null=True, backref='ttag_junctions')
    qa = ForeignKeyField(Qa, null=True, backref='ttag_junctions')
    duty = ForeignKeyField(Duty, null=True, backref='ttag_junctions')
    samplesheet = ForeignKeyField(SampleSheet, null=True, backref='ttag_junctions')
    sample = ForeignKeyField(Sample, null=True, backref='ttag_junctions')
    file = ForeignKeyField(File, null=True, backref='ttag_junctions')

JobFileJunction = File._duties.get_through_model()


REGISTRY = [Tag, Run, Qa, Duty, SampleSheet, Sample, File, TagJunction, JobFileJunction, TripleTag, TTagJunction]
