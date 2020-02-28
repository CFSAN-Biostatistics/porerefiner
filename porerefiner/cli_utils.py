"Custom argument handler types for Click"

import click
import csv
import datetime
import json
import sys
from pathlib import Path
from contextlib import contextmanager
from functools import wraps, partial
from io import TextIOWrapper


from grpclib.client import Channel, GRPCError

from tabulate import tabulate
from xml.etree import ElementTree as xml
from xml.dom import minidom
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

class PathPath(click.Path):

    def convert(self, value, param, ctx):
        val = super().convert(value, param, ctx)
        return Path(val)


def handle_connection_errors(func):
    @wraps(func)
    def wrapper(*a, **k):
        try:
            return func(*a, **k)
        except ConnectionRefusedError:
            print("ERROR: Connection to porerefiner service refused. Is the service running?", file=stderr)
            quit(61)
        except FileNotFoundError as e:
            print(f"ERROR: Socket file not found at configured path. Has the service ever been started?", file=stderr)
            quit(e.errno)
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
            for file in run.files:
                rec.append(dict(id='-',
                                name=file.name,
                                path=file.path,
                                status=('UNREADY', 'READY')[file.ready],
                                tags=",".join(file.tags)))
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
def xml_formatter(extend=False): #TODO
    rec = xml.Element('root')
    def print_run(run):
        r = xml.SubElement(rec, 'run')
        xml.SubElement(r, 'id').text = str(run.id)
        xml.SubElement(r, 'name').text = run.name
        xml.SubElement(r, 'nickname').text = run.mnemonic_name
        xml.SubElement(r, 'status').text = run.status
        xml.SubElement(r, 'path').text = run.path
        xml.SubElement(r, 'basecallingModel').text = run.basecalling_model

        s = xml.SubElement(r, 'samples')
        for sample in run.samples:
            sa = xml.SubElement(s, 'sample')
            xml.SubElement(sa, 'id').text = str(sample.id)
            xml.SubElement(sa, 'name').text = sample.name
            xml.SubElement(sa, 'accession').text = sample.accession
            xml.SubElement(sa, 'barcodeId').text = sample.barcode_id
            xml.SubElement(sa, 'organism').text = sample.organism
            xml.SubElement(sa, 'comment').text = sample.comment
            xml.SubElement(sa, 'user').text = sample.user
            f = xml.SubElement(sa, 'files')
            for file in sample.files:
                fi = xml.SubElement(f, 'file')
                xml.SubElement(fi, 'name').text = file.name
                xml.SubElement(fi, 'path').text = file.path
                xml.SubElement(fi, 'status').text = ('UNREADY', 'READY')[file.ready]
                xml.SubElement(fi, 'hash').text = file.hash
                t = xml.SubElement(fi, 'tags')
                for tag in file.tags:
                    xml.SubElement(t, 'tag').text = tag
            t = xml.SubElement(sa, 'tags')
            for tag in sample.tags:
                xml.SubElement(t, 'tag').text = tag


        f = xml.SubElement(r, 'files')
        for file in run.files:
            fi = xml.SubElement(f, 'file')
            xml.SubElement(fi, 'name').text = file.name
            xml.SubElement(fi, 'path').text = file.path
            xml.SubElement(fi, 'status').text = ('UNREADY', 'READY')[file.ready]
            xml.SubElement(fi, 'hash').text = file.hash
            t = xml.SubElement(fi, 'tags')
            for tag in file.tags:
                xml.SubElement(t, 'tag').text = tag

        t = xml.SubElement(r, 'tags')
        for tag in run.tags:
            xml.SubElement(t, 'tag').text = tag

    yield print_run
    pretty = minidom.parseString(xml.tostring(rec, 'utf-8'))
    click.echo(pretty.toprettyxml(indent='  '))
    #xml.ElementTree(rec).write(sys.stdout, encoding='unicode', xml_declaration=True)


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
    rows = (tuple(c.value for c in row) for row in book.worksheets[0].iter_rows())
    _, ss.porerefiner_ver, *_ = next(rows)
    if ss.porerefiner_ver == '1.0.0':
        ss.date.GetCurrentTime()
        _, ss.library_id, *_ = next(rows)
        _, ss.sequencing_kit, *_ = next(rows)
        next(rows) # ditch the header
        for sample_id, accession, barcode_id, organism, extraction_kit, comment, user, *_ in rows:
            ss.samples.add(sample_id=sample_id,
                           accession=accession,
                           barcode_id=str(barcode_id),
                           organism=organism,
                           extraction_kit=extraction_kit,
                           comment=comment,
                           user=user)
        #[ss.samples.add(*(cell.value for cell in row[:6])) for row in rows]

    else:
        raise ValueError(f"Sample sheet of version {ss.porerefiner_ver} not supported.")

    return ss

