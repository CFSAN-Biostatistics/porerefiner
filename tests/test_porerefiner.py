#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `porerefiner` package."""

from unittest import TestCase, skip

from click.testing import CliRunner

from porerefiner import porerefiner
from porerefiner import cli
from porerefiner import models

from shutil import rmtree

from tempfile import mkdtemp

from hypothesis import given
import hypothesis.strategies as strat
from hypothesis_fspaths import fspaths

import asyncio
from asyncio import run as _run

from datetime import datetime, timedelta

# def run(task):
#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(task)

RUN_PK = 100
RUN_NAME = 'TEST_TEST'

class TestCoreFunctions(TestCase):

    def setUp(self):
        models._db.init(":memory:", pragmas={'foreign_keys':1})
        [cls.create_table() for cls in models.REGISTRY]
        self.flow = flow = models.Flowcell.create(consumable_id="TEST|TEST|TEST", consumable_type="TEST|TEST|TEST", path="TEST/TEST/TEST")
        self.run = models.Run.create(pk=RUN_PK, library_id='x', name=RUN_NAME, flowcell=flow, path="TEST/TEST/TEST")
        self.file = models.File.create(run=self.run, path='TEST/TEST/TEST/TEST', last_modified=datetime.now() - timedelta(hours=2))

    def tearDown(self):
        pass

    def test_get_run(self):
        run1 = porerefiner.get_run(RUN_PK)
        run2 = porerefiner.get_run(RUN_NAME)
        assert run1 == run2

    @given(strat.one_of(strat.text(max_size=30), strat.integers(min_value=-2**16, max_value=2**16)))
    def test_fail_get_run(self, runid):
        with self.assertRaises(ValueError):
            run = porerefiner.get_run(runid)

    @skip('not implemented')
    @given(fspaths().filter(lambda p: p))
    def test_register_new_run(self, path):
        assert False

    def test_get_run_info(self):
        run1 = _run(porerefiner.get_run_info(RUN_PK))
        run2 = _run(porerefiner.get_run_info(RUN_NAME))

    @given(strat.one_of(strat.text(max_size=30), strat.integers(min_value=-2**16, max_value=2**16)))
    def test_fail_get_run_info(self, run_id):
        with self.assertRaises(ValueError):
            _run(porerefiner.get_run_info(run_id))

    #@skip('not implemented')
    def test_list_runs(self):
        self.assertEqual(len(_run(porerefiner.list_runs())), 1)

    #@skip('not implemented')
    def test_poll_active_run(self):
        _end_run = porerefiner.end_run
        signal = False
        async def mock(*a, **k):
            nonlocal signal
            signal = True
        porerefiner.end_run = mock
        self.assertEquals(_run(porerefiner.poll_active_run()), 1) #checked 1 file
        #self.assertIn(self.file, self.run.files)
        #self.assertGreater(datetime.now() - self.run.files[0].last_modified, timedelta(hours=1))
        assert signal #ran end_run
        porerefiner.end_run = _end_run


    @skip('not implemented')
    def test_end_run(self):
        assert False

    @skip('not implemented')
    def test_send_run(self):
        assert False



class TestPoreFSEventHander(TestCase):

    def setUp(self):
        models._db.init(":memory:", pragmas={'foreign_keys':1})
        [cls.create_table() for cls in models.REGISTRY]

    def tearDown(self):
        pass

    @skip('not implemented')
    @given(fspaths().filter(lambda p: p)) #non-blank paths
    def test_on_created(self, path):
        assert False

    @skip('not implemented')
    @given(fspaths().filter(lambda p: p))
    def test_on_modified(self, path):
        assert False

    @skip('not implemented')
    @given(fspaths().filter(lambda p: p))
    def test_on_deleted(self, path):
        assert False

class TestPoreDispatchServer(TestCase):
    def setUp(self):
        models._db.init(":memory:", pragmas={'foreign_keys':1})
        [cls.create_table() for cls in models.REGISTRY]

    def tearDown(self):
        pass

    @skip('not implemented')
    def test_get_runs(self):
        assert False

    @skip('not implemented')
    def test_get_run_info(self):
        assert False

    @skip('not implemented')
    def test_attach_sheet_run(self):
        assert False

    @skip('not implemented')
    def test_rsync_run_to(self):
        assert False

class TestServerStart(TestCase):

    def setUp(self):
        models._db.init(":memory:", pragmas={'foreign_keys':1})
        [cls.create_table() for cls in models.REGISTRY]

    def tearDown(self):
        pass

    @skip('not implemented')
    def test_start_fs_watchdog(self):
        assert False

    @skip('not implemented')
    def test_start_server(self):
        assert False
