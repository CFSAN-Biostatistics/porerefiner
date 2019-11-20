# -*- coding: utf-8 -*-

"""Unit test package for porerefiner."""

# from hypothesis_fspaths import fspaths

#safe_paths = lambda: fspaths().filter(lambda x: isinstance(x, str) or hasattr(x, '__fspath__'))

from unittest import TestCase

from hypothesis.strategies import text, characters, composite, one_of, just, builds, integers, datetimes, emails, text, lists
from pathlib import Path
import os

from porerefiner import models

from peewee import SqliteDatabase

from porerefiner.protocols.porerefiner.rpc import porerefiner_pb2 as messages

# SQLite can't accept a 32-bit integer
sql_ints = lambda: integers(min_value=-2**16, max_value=2**16)

@composite
def paths(draw, under=""):
    r = just(under)
    m = text(min_size=1)
    n = text(min_size=1)
    p = builds(Path, r, m, n)
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
    sam = lists(samples(), min_size=1, unique_by=(lambda s: s.sample_id, lambda s: s.accession), max_size=12)
    ss = draw(builds(messages.SampleSheet,
                     porerefiner_ver=ver,
                     library_id=lib,
                     sequencing_kit=seq,
                     samples=sam))
    ss.date.FromDatetime(draw(dat))
    return ss



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
    print(samplesheets().example())
