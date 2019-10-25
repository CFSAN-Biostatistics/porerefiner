# -*- coding: utf-8 -*-

"""Unit test package for porerefiner."""

# from hypothesis_fspaths import fspaths

#safe_paths = lambda: fspaths().filter(lambda x: isinstance(x, str) or hasattr(x, '__fspath__'))

from unittest import TestCase

from hypothesis.strategies import text, composite, one_of, just, builds
from pathlib import Path
import os

from porerefiner import models

from peewee import SqliteDatabase

@composite
def paths(draw, under=""):
    r = just(under)
    m = text(min_size=1)
    n = text(min_size=1)
    p = builds(Path, r, m, n)
    return draw(one_of(p, p.map(str)))


class TestBase(TestCase):

    def setUp(self):
        self.db = SqliteDatabase(":memory:", pragmas={'foreign_keys':1})
        self.db.bind(models.REGISTRY, bind_refs=False, bind_backrefs=False)
        self.db.connect()
        self.db.create_tables(models.REGISTRY)

    def tearDown(self):
        #[cls.delete().where(True).execute() for cls in models.REGISTRY]
        self.db.close()
