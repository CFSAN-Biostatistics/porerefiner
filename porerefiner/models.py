from peewee import *
from config import config

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


class Run(PorerefinerModel): #TODO
    "A run is an annotated collection of files being produced"

    pk = AutoField()
    library_id = CharField()
    run_human_name = CharField(default = Run.create_readable_name)
    status = CharField(choices=PorerefinerModel.statuses)

    @staticmethod
    def create_readable_name():
        "Docker-style random name from namesgenerator"
        return namesgenerator.get_random_name()

class File(PorerefinerModel): #TODO
    "A file is a path on the filesystem"
    pk = AutoField()
    run = ForeignKeyField(Run, backref='files')
    path = CharField(index=True)


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

    @classmethod
    def from_csv(cls, path_to_file, delimiter=','):
        "import a sample sheet in csv/tsv format"
        pass

    @classmethod
    def from_excel(cls, path_to_file):
        "import a sample sheet in xlsx format"
        pass

class Sample(PorerefinerModel): #TODO
    "A sample is an entry originally from a sample sheet"
    pk = AutoField()
    name = CharField()
    samplesheet = ForeignKeyField(SampleSheet, backref='samples')
