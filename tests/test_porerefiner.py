#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `porerefiner` package."""

from unittest import TestCase, skip, Mock, patch
#from unittest.mock import AsyncMock
from asyncmock import AsyncMock

from click.testing import CliRunner

from porerefiner import porerefiner
from porerefiner import cli
from porerefiner import models
from porerefiner.cli_utils import absolutize_path as ap, relativize_path as rp
from tests import paths, with_database, TestBase as DBSetupTestCase

from shutil import rmtree

from os.path import split

from tempfile import mkdtemp

from hypothesis import given
import hypothesis.strategies as strat
#from hypothesis_fspaths import fspaths

import asyncio
#from asyncio import run as _run

import pathlib
import os, sys

from datetime import datetime, timedelta

def _run(task):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(task)


RUN_PK = 100
RUN_NAME = 'TEST_TEST'

class TestCoreFunctions(DBSetupTestCase):

    def setUp(self):
        super().setUp()
        self.flow = flow = models.Flowcell.create(consumable_id="TEST|TEST|TEST", consumable_type="TEST|TEST|TEST", path="TEST/TEST/TEST")
        self.run = models.Run.create(pk=RUN_PK, library_id='x', name=RUN_NAME, flowcell=flow, path="TEST/TEST/TEST")
        self.file = models.File.create(run=self.run, path='TEST/TEST/TEST/TEST', last_modified=datetime.now() - timedelta(hours=2))


    def test_get_run(self):
        run1 = porerefiner.get_run(RUN_PK)
        run2 = porerefiner.get_run(RUN_NAME)
        assert run1 == run2

    # @given(fspaths())
    # def test_fs_paths(self, path):
    #     pathlib.Path(bytes.decode(path))


    @given(strat.one_of(strat.text(max_size=30), strat.integers(min_value=-2**16, max_value=2**16)))
    def test_fail_get_run(self, runid):
        with self.assertRaises(ValueError):
            run = porerefiner.get_run(runid)

    @skip('not implemented')
    @given(paths())
    def test_register_new_run(self, path):
        assert False

    def test_get_run_info(self):
        run1 = _run(porerefiner.get_run_info(RUN_PK))
        run2 = _run(porerefiner.get_run_info(RUN_NAME))
        self.assertEqual(run1, run2)

    @given(strat.one_of(strat.text(max_size=30), strat.integers(min_value=-2**16, max_value=2**16)))
    def test_fail_get_run_info(self, run_id):
        with self.assertRaises(ValueError):
            _run(porerefiner.get_run_info(run_id))

    #@skip('not implemented')
    def test_list_runs(self):
        self.assertEqual(len(_run(porerefiner.list_runs(all=True))), 1)

    def test_list_runs_running(self):
        models.Run.create(library_id='x', name=RUN_NAME, flowcell=self.flow, path="TEST/TEST/TEST", ended=datetime.now())
        self.assertEqual(len(_run(porerefiner.list_runs())), 1)

    def test_list_runs_tags(self):
        tag = models.Tag.create(name='TEST')
        models.TagJunction.create(tag=tag, run=self.run)
        self.assertEqual(len(_run(porerefiner.list_runs(tags=['TEST', 'other tag']))), 1)


    #@skip('not implemented')
    def test_poll_active_run(self):
        _end_run = porerefiner.end_run
        signal = False
        async def mock(*a, **k):
            nonlocal signal
            signal = True
        porerefiner.end_run = mock
        self.assertEqual(_run(porerefiner.poll_active_run()), 1) #checked 1 file
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

    class FakeEvent:
        def __init__(self, path, is_dir=True):
            self.src_path = path
            self.is_directory = is_dir

    def setUp(self):
        super().setUp()


    #@skip('not implemented')
    @given(flowcell_path=paths())
    @with_database
    def test_on_created_flowcell(self, flowcell_path):
        path = pathlib.Path(flowcell_path)
        ut = porerefiner.PoreRefinerFSEventHandler(path.parent)
        event = self.FakeEvent(flowcell_path)
        _reg_flow = porerefiner.register_new_flowcell
        mock = AsyncMock()
        porerefiner.register_new_flowcell = mock
        _run(ut.on_created(event))
        porerefiner.register_new_flowcell = _reg_flow
        mock.assert_called_once()

    #@skip('not implemented')
    @given(flowcell_path=paths(under='TEST'))
    @with_database
    def test_on_created_run(self, flowcell_path):
        path = pathlib.Path(flowcell_path)
        ut = porerefiner.PoreRefinerFSEventHandler(path.parent)
        models.Flowcell.get_or_create(pk=RUN_PK+1, consumable_id="TEST|TEST|TEST", consumable_type="TEST|TEST|TEST", path=path)
        event = self.FakeEvent(path / 'TEST')
        self.assertIsNone(models.Run.get_or_none(models.Run.path == rp(event.src_path)))
        _reg_run = porerefiner.register_new_run
        mock = AsyncMock()
        porerefiner.register_new_run = mock
        _run(ut.on_created(event))
        porerefiner.register_new_run = _reg_run
        mock.assert_called_once()

    # @skip('not implemented')
    @given(path=paths(under='TEST/TEST'))
    @with_database
    def test_on_created_file(self, path):
        ut = porerefiner.PoreRefinerFSEventHandler(split(split(split(path)[0])[0])[0])
        flow = models.Flowcell.create(pk=RUN_PK+1,
                                      consumable_id='TEST',
                                      consumable_type='TEST',
                                      path=rp(split(split(path)[0])[0]))
        run = models.Run.create(pk=RUN_PK, library_id='x', name=RUN_NAME, flowcell=flow, path=rp(split(path)[0]))
        event = self.FakeEvent(rp(path), is_dir=False)
        _run(ut.on_created(event))
        self.assertEqual(len(run.files), 1)
        self.assertEqual(len(list(models.File.select().where(models.File.path == path))), 1)

    @skip('not implemented')
    @patch('porerefiner.File')
    def test_on_modified(self, mock):
        event = self.FakeEvent('TEST', True)
        _run(porerefiner.on_modified(event))
        self.assertFalse(mock.get_or_none.called())

    @skip('not implemented')
    @given(paths())
    def test_on_deleted(self, path):
        assert False

class TestPoreDispatchServer(DBSetupTestCase):

    def setUp(self):
        super().setUp()
        self.flow = flow = models.Flowcell.create(consumable_id="TEST|TEST|TEST", consumable_type="TEST|TEST|TEST", path="TEST/TEST/TEST")
        self.run = models.Run.create(pk=RUN_PK, library_id='x', name=RUN_NAME, flowcell=flow, path="TEST/TEST/TEST")
        self.file = models.File.create(run=self.run, path='TEST/TEST/TEST/TEST', last_modified=datetime.now() - timedelta(hours=2))
        self.tag = models.Tag.create(name='TEST')
        models.TagJunction.create(tag=tag, run=self.run)

    @skip('no test')
    def test_get_runs_default(self):
        assert False

    @skip('no test')
    def test_get_runs_all(self):
        assert False

    @skip('no test')
    def test_get_runs_tags(self):
        assert

    @skip('no test')
    def test_get_run_info(self):
        assert False

    @skip('no test')
    def test_attach_sheet_run(self):
        assert False

    @skip('not implemented')
    def test_rsync_run_to(self):
        assert False

class TestServerStart(TestCase):


    @skip('not implemented')
    def test_start_fs_watchdog(self):
        assert False

    @skip('not implemented')
    def test_start_server(self):
        assert False
