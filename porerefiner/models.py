from peewee import *
#from porerefiner.config import config

import asyncio
import datetime
import pathlib
import pickle
import namesgenerator
import sys

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
        return [tag_j.tag for tag_j in self.tag_junctions]


class Tag(BaseModel):
    "A tag is an informal annotation"

    name = CharField(null=False, constraints=[Check("name != '' ")])

class PathField(Field):

    field_type = 'blob'

    def db_value(self, value):
        if hasattr(value, '__fspath__'):
            value = str(value)
        if isinstance(value, bytes):
            value = value.decode(sys.getfilesystemencoding(), 'surrogateescape')
        return value

    def python_value(self, value):
        return pathlib.Path(value)



def create_readable_name():
    "Docker-style random name from namesgenerator"
    return namesgenerator.get_random_name()

class Flowcell(PorerefinerModel):
    "A flowcell is the disposable part of the sequencer"

    pk = AutoField()

    consumable_id = CharField(null=False)
    consumable_type = CharField(null=False)
    path = PathField(index=True)

class Run(PorerefinerModel):
    "A run is an annotated collection of files being produced"

    basecallers = [('BC', 'Basecallers')]

    pk = AutoField()

    flowcell = ForeignKeyField(Flowcell, backref='runs')
    _sample_sheet = DeferredForeignKey('SampleSheet', null=True, backref='runs')

    name = CharField()
    library_id = CharField()
    alt_name = CharField(default = create_readable_name)
    run_id = CharField(null=True)
    started = DateTimeField(default = datetime.datetime.now)
    ended = DateTimeField(null=True, default=None)
    status = CharField(choices=PorerefinerModel.statuses, default='RUNNING')
    path = PathField(index=True)
    # flowcell_type = CharField()
    # flowcell_id = CharField()
    basecalling_model = CharField(choices=basecallers, null=True)

    @property
    def run_duration(self):
        if self.ended:
            return self.ended - self.started

    @property
    def sample_sheet(self):
        return self._sample_sheet or SampleSheet()

    @property
    def samples(self):
        return self.sample_sheet.samples


class Qa(PorerefinerModel):
    "A QA is a set of quality-control analysis metrics"

    pk = AutoField()
    coverage = FloatField()
    quality = FloatField()


class Job(PorerefinerModel):
    "A job is a scheduled HPC job, pre or post submission"
    pk = AutoField()
    job_id = IntegerField()
    status = CharField(choices=PorerefinerModel.statuses)

class SampleSheet(PorerefinerModel):
    "A samplesheet is a particular file, eventually attached to a run"
    pk = AutoField()
    path = PathField(index=True)
    # run = ForeignKeyField(Run, backref='_sample_sheet', unique=True, null=True)
    date = DateField(null=True)
    sequencing_kit = CharField(null=True)

    @classmethod
    async def from_csv(cls, path_to_file, delimiter=','):
        "import a sample sheet in csv/tsv format"
        pass

    @classmethod
    async def from_excel(cls, path_to_file):
        "import a sample sheet in xlsx format"
        pass

class Sample(PorerefinerModel):
    "A sample is an entry originally from a sample sheet"

    BARCODES = {}

    pk = AutoField()
    sample_id = CharField(null=False)
    accession = CharField()
    barcode_id = IntegerField()
    #barcode_seq = CharField() #maybe set this when we load a sheet
    organism = CharField()
    extraction_kit = CharField()
    comment = CharField()
    user = CharField()




    samplesheet = ForeignKeyField(SampleSheet, backref='samples')

    @property
    def barcode_seq(self):
        return self.BARCODES.get(self.barcode_id, "")



class File(PorerefinerModel):
    "A file is a path on the filesystem"
    pk = AutoField()
    run = ForeignKeyField(Run, backref='files', null=True)
    sample = ForeignKeyField(Sample, backref='files', null=True)
    path = PathField(index=True, unique=True)
    checksum = CharField(index=True, null=True)
    last_modified = DateTimeField(default=datetime.datetime.now)
    exported = IntegerField(default=0)


class TagJunction(BaseModel):
    tag = ForeignKeyField(Tag)
    flowcell = ForeignKeyField(Flowcell, null=True, backref='tag_junctions')
    run = ForeignKeyField(Run, null=True, backref='tag_junctions')
    qa = ForeignKeyField(Qa, null=True, backref='tag_junctions')
    job = ForeignKeyField(Job, null=True, backref='tag_junctions')
    samplesheet = ForeignKeyField(SampleSheet, null=True, backref='tag_junctions')
    sample = ForeignKeyField(Sample, null=True, backref='tag_junctions')
    file = ForeignKeyField(File, null=True, backref='tag_junctions')


REGISTRY = [Tag, Flowcell, Run, Qa, Job, SampleSheet, Sample, File, TagJunction]
