# -*- coding: utf-8 -*-

"""Unit test package for porerefiner."""

# from hypothesis_fspaths import fspaths

#safe_paths = lambda: fspaths().filter(lambda x: isinstance(x, str) or hasattr(x, '__fspath__'))

import asyncio

from unittest import TestCase

from collections import namedtuple
from datetime import datetime
from hypothesis.strategies import text, characters, composite, one_of, just, builds, integers, datetimes, emails, text, lists, booleans
from pathlib import Path
import os

from porerefiner import models

from peewee import SqliteDatabase

from porerefiner.protocols.porerefiner.rpc import porerefiner_pb2 as messages

# SQLite can't accept a 32-bit integer
sql_ints = lambda: integers(min_value=-2**16, max_value=2**16)

def _run(task):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(task)

@composite
def paths(draw, under="", min_deep=2, pathlib_only=False):
    r = [just(under)]
    for _ in range(min_deep):
        r.append(text(min_size=1, max_size=255))
    p = builds(Path, *r)
    if pathlib_only:
        return draw(p)
    return draw(one_of(p, p.map(str)))

@composite
def samples(draw):
    sid = text(min_size=7, max_size=10)
    acc = text(min_size=5, max_size=10)
    bar = text(min_size=10, max_size=10)
    org = text(min_size=12, max_size=12)
    ext = text(min_size=10, max_size=10)
    com = text()
    use = emails()
    return draw(builds(messages.SampleSheet.Sample,
                       sample_id=sid,
                       accession=acc,
                       barcode_id=bar,
                       organism=org,
                       extraction_kit=ext,
                       comment=com,
                       user=use))

@composite
def samplesheets(draw):
    ver = just('1.0.0')
    dat = datetimes()
    lib = text(min_size=12, max_size=12)
    seq = text(min_size=12, max_size=12)
    sam = lists(samples(), min_size=1, max_size=12)
    ss = draw(builds(messages.SampleSheet,
                     porerefiner_ver=ver,
                     library_id=lib,
                     sequencing_kit=seq,
                     samples=sam))
    ss.date.FromDatetime(draw(dat))
    return ss


@composite
def flowcells(draw, path=None):
    pk  = sql_ints()
    cid = text()
    cty = text()
    if not path:
        pat = paths()
    else:
        pat = just(Path(path))
    return draw(builds(models.Flowcell,
                       pk=pk,
                       consumable_id=cid,
                       consumable_type=cty,
                       path=pat))

@composite
def runs(draw, sheet=True):
    if sheet:
        ss = samplesheets()
    else:
        ss = just(None)
    path = draw(paths())
    return draw(builds(models.Run,
                       flowcell=flowcells(path=path.parent),
                       _sample_sheets=ss,
                       name=text(),
                       library_id=text(),
                       run_id=text(),
                       started=datetimes(max_value=datetime.now()),
                       ended=datetimes(min_value=datetime.now()),
                       status=one_of(*[just(status) for status in models.Run.statuses]),
                       path=path,
                       basecalling_model=one_of(*[just(model[0]) for model in models.Run.basecallers])))

Event = namedtuple('Event', ('src_path', 'is_directory'))

@composite
def fsevents(draw, min_deep=3):
    return draw(builds(Event,
                       src_path=paths(min_deep=min_deep, pathlib_only=True),
                       is_directory=booleans()))

class TestBase(TestCase):

    def setUp(self):
        self.db = SqliteDatabase(":memory:", pragmas={'foreign_keys':1}, autoconnect=False)
        self.db.bind(models.REGISTRY, bind_refs=False, bind_backrefs=False)
        self.db.connect()
        self.db.create_tables(models.REGISTRY)

    def tearDown(self):
        #[cls.delete().where(True).execute() for cls in models.REGISTRY]
        self.db.drop_tables(models.REGISTRY)
        self.db.close()

from functools import wraps

def with_database(func):
    @wraps(func)
    def wrapped_test_function(*a, **k):
        db = SqliteDatabase(":memory:", pragmas={'foreign_keys':1}, autoconnect=False)
        db.bind(models.REGISTRY, bind_refs=False, bind_backrefs=False)
        db.connect()
        db.create_tables(models.REGISTRY)
        try:
            return func(*a, **k)
        finally:
            db.drop_tables(models.REGISTRY)
            db.close()
    return wrapped_test_function

if __name__ == '__main__':
    for symbol in locals().values():
        if hasattr(symbol, 'example'):
            print(symbol.example())
