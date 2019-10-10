from peewee import *
from porerefiner.config import config

import asyncio
import datetime
import namesgenerator

class PorerefinerModel(Model):
    "Abstract base class for PoreRefiner models"
    class Meta:
        db = SqliteDatabase(config['db'])

    statuses = (('READY', 'Ready to Run'),
                ('QUEUED', 'Scheduled to Run')
                ('RUNNING', 'Running'),
                ('STOPPING', 'Stopping'),
                ('DONE', 'Ended'),
                ('FAILED', 'Ended with Failure'))

    def to_json(self):
        pass


class Run(PorerefinerModel): #TODO
    "A run is an annotated collection of files being produced"

    pk = AutoField()
    library_id = CharField()
    human_name = CharField(default = Run.create_readable_name)
    run_id = CharField(null=True)
    started = DateTimeField(default = datetime.datetime.now)
    status = CharField(choices=PorerefinerModel.statuses)
    path = CharField(index=True)
    flowcell_type = CharField()
    flowcell_id = CharField()
    basecalling_model = CharField()

    @staticmethod
    def create_readable_name():
        "Docker-style random name from namesgenerator"
        return namesgenerator.get_random_name()

class QA(PorerefinerModel): #TODO
    "A QA is a set of quality-control analysis metrics"

    pk = AutoField()
    coverage = FloatField()
    quality = FloatField()


class Job(PorerefinerModel): #TODO
    "A job is a scheduled HPC job, pre or post submission"
    pk = AutoField()
    job_id = IntegerField()
    status = CharField(choices=PorerefinerModel.statuses)

class SampleSheet(PorerefinerModel): #TODO
    "A samplesheet is a particular file, eventually attached to a run"
    pk = AutoField()
    path = CharField(index=True)
    run = ForeignKeyField(Run, backref='samplesheet', unique=True, null=True)
    date = DateField()
    sequencing_kit = CharField()

    @classmethod
    async def from_csv(cls, path_to_file, delimiter=','):
        "import a sample sheet in csv/tsv format"
        pass

    @classmethod
    async def from_excel(cls, path_to_file):
        "import a sample sheet in xlsx format"
        pass

class Sample(PorerefinerModel): #TODO
    "A sample is an entry originally from a sample sheet"

    BARCODES = {}

    pk = AutoField()
    name = CharField()
    barcode_id = IntegerField()
    #barcode_seq = CharField() #maybe set this when we load a sheet
    cfsan_id = CharField(null=False)
    serotype = CharField()
    extraction_kit = CharField()



    samplesheet = ForeignKeyField(SampleSheet, backref='samples')

    @property
    def barcode_seq(self):
        return self.BARCODES.get(self.barcode_id, "")



class File(PorerefinerModel): #TODO
    "A file is a path on the filesystem"
    pk = AutoField()
    run = ForeignKeyField(Run, backref='files')
    sample = ForeignKeyField(Sample, backref='files', null=True)
    path = CharField(index=True, unique=True)
    checksum = CharField(index=True)
    last_modified = DateTimeField(default=datetime.datetime.now)
