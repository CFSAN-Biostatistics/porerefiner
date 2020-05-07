"Custom argument handler types for Click"

import click
import csv
import datetime
import json
import sys
from pathlib import Path
from contextlib import contextmanager
from collections import defaultdict
from dataclasses import MISSING
from functools import wraps, partial
from io import TextIOWrapper
from typing import List


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




class Email:
    pass

class Url:
    pass

class PathStr:
    pass


def render_dataclass(the_class):
    "Inspect dataclass fields and print some helpful text"
    sample_values = defaultdict(lambda: "<some_value>")
    sample_values.update({str:'"some string"',
                          int:"123",
                          float:"123.45",
                          dict:"{key1:val1, key2:val2}",
                          Email:"eee@mail.net",
                          Url:"http://server.serv/path",
                          PathStr:"path/to/some/file",
                          List[str]:"[<string>,...]",
                          List[Email]:"[aaa@mail.net, bbb@mail.net, ...]",
                          List[int]:"[<integer>,...]",
                          List[Url]:"[http://server.co, http://serv.cc, ...]",
                          List[PathStr]:"[path/aaa, path/bbb, ...]"})
    nw = max([len(field.name) for field in the_class.__dataclass_fields__.values()])
    tw = max([len(str(field.type)) for field in the_class.__dataclass_fields__.values() if field.name != 'submitter'])
    options = f"{'param_name':<{nw}}\t{'type':<{tw}}\texample"
    for field in the_class.__dataclass_fields__.values():
        if field.name != 'submitter':
            name = f"{field.name:<{nw}}"
            _type = f"{str(field.type):<{tw}}"
            example = (str(field.default), sample_values[field.type])[type(field.default) is not MISSING]
            options += f"\n\t{name}\t{_type}\t{example}"
    # options += "\n\t".join([f"{field.name:<{nw}}\t{str(field.type):<{tw}}\t{sample_values[field.type]}" for field in the_class.__dataclass_fields__.values() if field.name is not 'submitter'])
    return f"""
classname: {the_class.__name__}

{the_class.__doc__}

configurable options:

\t{options}
"""
