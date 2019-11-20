#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `porerefiner` package."""

from unittest import TestCase, skip
from unittest.mock import Mock, patch
#from unittest.mock import AsyncMock
from asyncmock import AsyncMock
from aiounittest import async_test

from click.testing import CliRunner

from porerefiner import porerefiner
from porerefiner import cli
from porerefiner import models
from porerefiner.cli_utils import absolutize_path as ap, relativize_path as rp
from porerefiner.protocols.porerefiner.rpc import porerefiner_pb2 as messages
from tests import paths, with_database, TestBase as DBSetupTestCase, samplesheets, samples

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

from peewee import JOIN

def _run(task):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(task)


RUN_PK = 101
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


    def test_get_run_info(self):
        run1 = _run(porerefiner.get_run_info(RUN_PK))
        run2 = _run(porerefiner.get_run_info(RUN_NAME))
        self.assertEqual(run1, run2)

    @given(strat.one_of(
            strat.text(max_size=30).filter(lambda n: n != RUN_NAME),
            strat.integers(min_value=-2**16, max_value=2**16).filter(lambda n: n != RUN_PK)
            ))
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
    @patch('porerefiner.porerefiner.end_run', new_callable=AsyncMock)
    def test_poll_active_run(self, mock):
        #run = models.Run.get(models.Run.pk==RUN_PK)
        self.assertGreater(len(models.Run.select().where(models.Run.status == 'RUNNING')), 0)
        self.assertGreater(len(models.Run.get(models.Run.pk==RUN_PK).files), 0)
        self.assertEqual(_run(porerefiner.poll_active_run()), 1) #checked 1 file
        #self.assertGreater(len(run.files), 0)
        #self.assertGreater(len(list(models.Run.select(models.Run.ended.is_null(True)))), 0)
        #self.assertTrue(len(run.files) and all([datetime.now() - file.last_modified > timedelta(hours=1) for file in run.files]))
        mock.assert_called() #ran end_run


    #@skip('not implemented')
    def test_end_run(self):
        mock = AsyncMock()
        with patch('porerefiner.porerefiner.NOTIFIERS', new_callable=lambda: [mock]) as _:
            _run(porerefiner.end_run(self.run))
        self.assertAlmostEqual(datetime.now(), self.run.ended, delta=timedelta(seconds=1))
        mock.notify.assert_called()
        self.assertIn('finished', [str(tag) for tag in self.run.tags])

    @skip('not implemented')
    def test_send_run(self):
        assert False

class TestNewRunRegistration(TestCase):

        # @skip('not working')
    @given(run_path=paths(),
           path=paths(),
           date=strat.datetimes(),
           sequencing_kit=strat.text())
    @with_database
    def test_register_new_run(self, run_path, **sam):
        ss = models.SampleSheet.create(**sam)
        query = models.SampleSheet.get_unused_sheets()
        self.assertEqual(query.count(), 1) #assert pre-state

        run = _run(porerefiner.register_new_run(pathlib.Path(run_path)))

        self.assertEqual(run.sample_sheet, ss)

        query = models.SampleSheet.get_unused_sheets()
        self.assertEqual(query.count(), 0) #assert test



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
        with patch('porerefiner.porerefiner.register_new_flowcell', new_callable=AsyncMock) as mock:
            path = pathlib.Path(flowcell_path)
            ut = porerefiner.PoreRefinerFSEventHandler(path.parent)
            event = self.FakeEvent(flowcell_path)
            _run(ut.on_created(event))
        mock.assert_called_once()

    # # @skip('not implemented')
    # # @given(flowcell_path=paths(under='/A/B/C'))
    # @with_database
    # def test_on_created_run(self, flowcell_path='/A/B/C/D'):
    #     path = pathlib.Path(flowcell_path)
    #     ut = porerefiner.PoreRefinerFSEventHandler(path.parent.parent)
    #     models.Flowcell.get_or_create(pk=RUN_PK+1, consumable_id="TEST|TEST|TEST", consumable_type="TEST|TEST|TEST", path=path)
    #     event = self.FakeEvent(path / 'TEST')
    #     self.assertIsNone(models.Run.get_or_none(models.Run.path == rp(event.src_path)))
    #     with patch('porerefiner.porerefiner.register_new_run', new_callable=AsyncMock) as mock:
    #         _run(ut.on_created(event))
    #     mock.assert_called_once()

    @with_database
    @patch('porerefiner.porerefiner.register_new_run', new_callable=AsyncMock)
    def test_on_created_run_simple(self, mock, path=pathlib.Path('/A/B/C/D/E')):
        ut = porerefiner.PoreRefinerFSEventHandler(path.parent.parent)
        event = self.FakeEvent(path)
        _run(ut.on_created(event))
        mock.assert_called_once()

    @with_database
    @patch('porerefiner.porerefiner.register_new_run', new_callable=AsyncMock)
    def test_on_created_run_deep(self, mock, path=pathlib.Path('/A/B/C/D/E')):
        ut = porerefiner.PoreRefinerFSEventHandler(path.parent.parent.parent)
        event = self.FakeEvent(path)
        _run(ut.on_created(event))
        mock.assert_not_called()

    @with_database
    @patch('porerefiner.porerefiner.register_new_run', new_callable=AsyncMock)
    @patch('porerefiner.porerefiner.File')
    def test_on_created_file_simple(self, mock_f, mock, path=pathlib.Path('/A/B/C/D/E')):
        ut = porerefiner.PoreRefinerFSEventHandler(path.parent.parent.parent)
        event = self.FakeEvent(path, is_dir=False)
        _run(ut.on_created(event))
        mock.assert_called_once()
        mock_f.get_or_create.assert_called_once()
    # @skip('not implemented')
    #@given(path=paths(under='TEST/TEST'))
    @with_database
    def test_on_created_file(self, path='/A/B/C/D/E'):
        path = pathlib.Path(path)
        ut = porerefiner.PoreRefinerFSEventHandler(path.parent.parent.parent)
        flow = models.Flowcell.create(pk=RUN_PK+1,
                                      consumable_id='TEST',
                                      consumable_type='TEST',
                                      path=rp(path.parent.parent))
        run = models.Run.create(pk=RUN_PK, library_id='x', name=RUN_NAME, flowcell=flow, path=rp(path.parent))
        event = self.FakeEvent(rp(path), is_dir=False)
        _run(ut.on_created(event))
        self.assertEqual(len(run.files), 1)
        self.assertEqual(len(list(models.File.select().where(models.File.path == path))), 1)

    @with_database
    def test_on_created_file_deep(self, path=pathlib.Path('/A/B/C/D/E')):
        ut = porerefiner.PoreRefinerFSEventHandler(path.parent.parent.parent) #A/B
        event = self.FakeEvent(path / 'test', is_dir=False) #E/test
        flow = models.Flowcell.create(pk=RUN_PK+1,
                                consumable_id='TEST',
                                consumable_type='TEST',
                                path=rp(path.parent.parent)) #A/B/C
        run = models.Run.create(pk=RUN_PK, library_id='x', name=RUN_NAME, flowcell=flow, path=rp(path.parent)) #A/B/C/D
        _run(ut.on_created(event))
        self.assertEqual(len(run.files), 1)
        self.assertEqual(len(list(models.File.select().where(models.File.path == event.src_path))), 1)

    # @skip('not implemented')
    @patch('porerefiner.porerefiner.File')
    def test_on_modified(self, mock):
        ut = porerefiner.PoreRefinerFSEventHandler(pathlib.Path('TEST'))
        event = self.FakeEvent('TEST', False)
        _run(ut.on_modified(event))
        mock.get_or_none.assert_called()

    @skip('not implemented')
    @given(paths())
    def test_on_deleted(self, path):
        assert False

class TestPoreDispatchServer(TestCase):

    # def setUp(self):
    #     super().setUp()
    #     self.flow = flow = models.Flowcell.create(consumable_id="TEST|TEST|TEST", consumable_type="TEST|TEST|TEST", path="TEST/TEST/TEST")
    #     self.run = models.Run.create(pk=RUN_PK, library_id='x', name=RUN_NAME, flowcell=flow, path="TEST/TEST/TEST")
    #     self.file = models.File.create(run=self.run, path='TEST/TEST/TEST/TEST', last_modified=datetime.now() - timedelta(hours=2))
    #     self.tag = models.Tag.create(name='TEST')
    #     models.TagJunction.create(tag=tag, run=self.run)

    @skip('no test')
    def test_get_runs_default(self):
        assert False

    @skip('no test')
    def test_get_runs_all(self):
        assert False

    @skip('no test')
    def test_get_runs_tags(self):
        assert False

    @skip('no test')
    def test_get_run_info(self):
        assert False

    # @skip('no test')
    @given(ss=samplesheets())
    @with_database
    def test_attach_sheet_run_no_run(self, ss):
        ut = porerefiner.PoreRefinerDispatchServer()
        strm = AsyncMock()
        strm.recv_message.return_value = messages.RunAttachRequest(sheet=ss)
        _run(ut.AttachSheetToRun(strm))
        strm.send_message.assert_called_once()

    @given(ss=samplesheets())
    @with_database
    def test_attach_sheet_to_run(self, ss):
        self.flow = flow = models.Flowcell.create(consumable_id="TEST|TEST|TEST", consumable_type="TEST|TEST|TEST", path="TEST/TEST/TEST")
        self.run = models.Run.create(pk=RUN_PK, library_id='x', name=RUN_NAME, flowcell=flow, path="TEST/TEST/TEST")
        self.file = models.File.create(run=self.run, path='TEST/TEST/TEST/TEST', last_modified=datetime.now() - timedelta(hours=2))
        ut = porerefiner.PoreRefinerDispatchServer()
        strm = AsyncMock()
        strm.recv_message.return_value = messages.RunAttachRequest(sheet=ss, id=RUN_PK)
        _run(ut.AttachSheetToRun(strm))
        strm.send_message.assert_called_once()

    @skip('not implemented')
    def test_rsync_run_to(self):
        assert False


class TestServerStart(TestCase):

    @skip('no test')
    def test_start_fs_watchdog(self):
        assert False

    #@skip('no test')
    @patch('porerefiner.porerefiner.graceful_exit')
    @patch('porerefiner.porerefiner.Server')
    def test_start_server(self, mock, _):
        mock.return_value = coro = AsyncMock()
        _run(porerefiner.start_server(None))
        mock.assert_called()
        coro.start.assert_called()
        coro.wait_closed.assert_called()

    #@skip('no test')
    @async_test
    async def test_start_run_end_polling(self):
        with patch('porerefiner.porerefiner.poll_active_run') as mock:
            task = await porerefiner.start_run_end_polling(0)
            await asyncio.sleep(5)
            task.cancel()
            mock.assert_called()

    #@skip('no test')
    @async_test
    async def test_start_job_polling(self):
        with patch('porerefiner.porerefiner.poll_jobs') as mock:
            task = await porerefiner.start_job_polling(0)
            await asyncio.sleep(5)
            task.cancel()
            mock.assert_called()
