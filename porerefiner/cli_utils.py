"Custom argument handler types for Click"

import click
import csv
import datetime
import json
from pathlib import Path
from contextlib import contextmanager
from functools import wraps, partial
from io import TextIOWrapper


from grpclib.client import Channel, GRPCError

from tabulate import tabulate
from xml.etree import ElementTree as xml
from sys import stderr

from porerefiner.protocols.porerefiner.rpc.porerefiner_grpc import PoreRefinerStub
from porerefiner.protocols.porerefiner.rpc.porerefiner_pb2 import SampleSheet

#these two functions are hooks in case we decide to store only relative paths.
#paths going into the database will be relativized; paths going out will be
#absolutized.
#Whatever they do, they need to invert each other
def relativize_path(path):
    if isinstance(path, str):
        return Path(path)
    return path

def absolutize_path(path):
    if hasattr(path, '__fspath__'):
        return str(path)
    return path

class RunID:
    "can be either a string name or a numeric id"

    RUN_NAME = 'RUN_NAME'
    RUN_ID = 'RUN_ID'

    def __init__(self, the_value):
        if isinstance(the_value, str):
            self.val_type = self.RUN_NAME
        elif isinstance(the_value, int):
            self.val_type = self.RUN_ID
        else:
            raise ValueError("value must be str or int")



class ValidRunID(click.ParamType):

    def convert(self, value, param, ctx):
        try:
            return int(value)
        except ValueError:
            return str(value)

VALID_RUN_ID = ValidRunID()


def handle_connection_errors(func):
    @wraps(func)
    def wrapper(*a, **k):
        try:
            return func(*a, **k)
        except ConnectionRefusedError:
            print("ERROR: Connection to porerefiner service refused. Is the service running?", file=stderr)
            quit(61)
    return wrapper


# Channel context manager for CLI utils

@contextmanager
def server(config_file):
    from porerefiner.config import Config
    config = Config(config_file, client_only=True).config
    channel = Channel(path=config['server']['socket'], ssl=config['server']['use_ssl'])
    client = PoreRefinerStub(channel)
    try:
        yield client
    except GRPCError as e:
        raise
    finally:
        channel.close()

#formatters for run output

@contextmanager
def hr_formatter(extend=False):
    rec = []
    def print_run(run):
        rec.append(dict(id=run.id,
                        name=run.name,
                        nickname=run.mnemonic_name,
                        status=run.status,
                        samples=len(run.samples),
                        files=sum([len(sam.files) for sam in run.samples]) + len(run.files),
                        tags=",".join(run.tags)))
        if extend:
            rec[-1]['path'] = run.path
            rec[-1]['flowcell'] = run.flowcell_id
            for sample in run.samples:
                rec.append(dict(id=sample.id,
                                name=sample.name,
                                nickname=sample.accession,
                                barcode_id=sample.barcode_id,
                                organism=sample.organism,
                                comment=sample.comment,
                                user=sample.user,
                                files=len(sample.files),
                                tags=",".join(sample.tags)))
    yield print_run
    print(tabulate(rec, headers="keys"))

class MessageAwareEncoder(json.JSONEncoder):

    def default(self, o):
        from google.protobuf.json_format import MessageToDict
        from google.protobuf.message import Message
        if isinstance(o, Message):
            return MessageToDict(o)
        return json.JSONEncoder.default(self, o)


@contextmanager
def json_formatter(extend=False):
    rec = []
    def print_run(run):
        rec.append(run)
    yield print_run
    click.echo(json.dumps(rec, cls=MessageAwareEncoder, indent=2))

@contextmanager
def xml_formatter(extend=False):
    rec = []
    def print_run(run):
        rec.append(run)
    yield print_run
    click.echo(xml.toString())


# We should do sample sheet parsing on the client side

def load_from_csv(file, delimiter=b',') -> SampleSheet:
    ss = SampleSheet()
    _, ss.porerefiner_ver, *_ = file.readline().split(delimiter)
    if ss.porerefiner_ver == '1.0.0':
        ss.date.GetCurrentTime()
        _, ss.library_id, *_ = file.readline().split(delimiter)
        _, ss.sequencing_kit, *_ = file.readline().split(delimiter)
        delimiter = delimiter.decode()
        [ss.samples.add(**row) for row in csv.DictReader(TextIOWrapper(file), delimiter=delimiter, dialect='excel')] #this should handle commas in fields
    else:
        raise ValueError(f"Sample sheet of version {ss.porerefiner_ver} not supported.")
    return ss

def load_from_excel(file) -> SampleSheet:
    import openpyxl
    ss = SampleSheet()
    book = openpyxl.load_workbook(file)
    rows = iter(book.rows)
    _, ss.porerefiner_ver, *_ = next(rows)
    if ss.porerefiner_ver == '1.0.0':
        ss.date.GetCurrentTime()
        _, ss.library_id, *_ = next(rows)
        _, ss.sequencing_kit, *_ = next(rows)
        next(rows)
        for sample_id, accession, barcode_id, organism, extraction_kit, comment, user in rows:
            ss.samples.add(sample_id, accession, barcode_id, organism, extraction_kit, comment, user)

    else:
        raise ValueError(f"Sample sheet of version {ss.porerefiner_ver} not supported.")

    return ss

