#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `porerefiner` package."""

# from unittest import TestCase, skip
from unittest.mock import Mock, patch
#from unittest.mock import AsyncMock
from mock import AsyncMock
# from aiounittest import async_test

from pytest import fixture, mark, raises

from click.testing import CliRunner

from porerefiner import porerefiner, fsevents as pr_fsevents, rpc
from porerefiner import cli
from porerefiner import models
from porerefiner import config
from porerefiner.cli_utils import absolutize_path as ap, relativize_path as rp
from porerefiner.protocols.porerefiner.rpc import porerefiner_pb2 as messages


from tests import paths, fsevents, Model, Message, db

from shutil import rmtree

from os.path import split

from tempfile import mktemp, mkdtemp, mkstemp, TemporaryDirectory, NamedTemporaryFile

from hypothesis import given, settings, HealthCheck
import hypothesis.strategies as strat
#from hypothesis_fspaths import fspaths

import asyncio
#from asyncio import run as _run

import pathlib
import os, sys

from datetime import datetime, timedelta

from peewee import JOIN


# RUN_PK = 101
# RUN_NAME = 'TEST_TEST'

@fixture
def run_pk():
    return 101

@fixture
def run_name():
    return "TEST_TEST"


@fixture
def tempdir():
    with TemporaryDirectory(delete=False) as t:
        pass
    yield t
    rmtree(t, ignore_errors=True)

@fixture
def run(db, run_pk, run_name, tempdir):
    r = models.Run.create(id=run_pk, library_id="x", name=run_name, path=tempdir)
    _, t = mkstemp(dir=tempdir)
    models.File.create(run=r, path=pathlib.Path(t), last_modified=datetime.now() - timedelta(hours=2))
    yield r



def test_get_run(run, run_pk, run_name):
    run1 = rpc.get_run(run_pk)
    run2 = rpc.get_run(run_name)
    assert run1 == run2

    # @given(fspaths())
    # def test_fs_paths(self, path):
    #     pathlib.Path(bytes.decode(path))


def test_fail_get_run(db):
    with raises(ValueError):
        rpc.get_run(10)

@mark.asyncio
async def test_rpc_get_run_info(run, run_pk, run_name):
    run1 = await rpc.get_run_info(run_pk)
    run2 = await rpc.get_run_info(run_name)
    assert run1 == run2

@mark.asyncio
async def test_fail_get_run_info(db):
    with raises(ValueError):
        await rpc.get_run_info(10)

#@skip('not implemented')
@mark.asyncio
async def test_list_runs(run):
    assert len(await rpc.list_runs(all=True)) == 1

@fixture
def ended_run(run, run_name):
    yield models.Run.create(library_id='x', name=run_name, path="TEST/TEST/TEST", ended=datetime.now())

@mark.asyncio
async def test_list_runs_running(ended_run):
    assert len(await rpc.list_runs(all=True)) == 2
    assert len(await rpc.list_runs()) == 1, "ended run was included"

@mark.asyncio
async def test_list_runs_tags(run):
    # tag = models.Tag.create(name='TEST')
    # ttag = models.TripleTag.create(namespace="TESTEST", name="TESTEST", value="TEST")
    # models.TagJunction.create(tag=tag, run=self.run)
    # models.TTagJunction.create(tag=ttag, run=self.run)
    run.tag("TEST")
    run.ttag(namespace="TEST", name="TEST", value="TEST")
    assert len(await rpc.list_runs(tags=['TEST', 'other tag'])) == 1


# #@skip('not implemented')
# @patch('porerefiner.fsevents.end_run', new_callable=AsyncMock)
# def test_poll_active_run(self, mock):
#     #run = models.Run.get(models.Run.pk==RUN_PK)
#     self.assertGreater(len(models.Run.select().where(models.Run.status == 'RUNNING')), 0)
#     self.assertGreater(len(models.Run.get(models.Run.pk==RUN_PK).files), 0)
#     self.assertEqual(_run(pr_fsevents.poll_active_run()), 1) #checked 1 file
#     #self.assertGreater(len(run.files), 0)
#     #self.assertGreater(len(list(models.Run.select(models.Run.ended.is_null(True)))), 0)
#     #self.assertTrue(len(run.files) and all([datetime.now() - file.last_modified > timedelta(hours=1) for file in run.files]))
#     mock.assert_called() #ran end_run


    # @skip('cant make this work with the database')
    # @with_database
    # def test_end_run(self):
    #     mock = AsyncMock()
    #     with patch('porerefiner.fsevents.NOTIFIERS', new_callable=lambda: [mock]) as _:
    #         _run(pr_fsevents.end_run(self.run))
    #     self.assertAlmostEqual(datetime.now(), self.run.ended, delta=timedelta(seconds=1))
    #     mock.notify.assert_called()
    #     self.assertIn('finished', [str(tag) for tag in self.run.tags])

    # @skip('not implemented')
    # def test_send_run(self):
    #     assert False

    # @patch('porerefiner.fsevents.SampleSheet')
    # @patch('porerefiner.fsevents.logging')
    # def test_register_new_run(self, log, mock):
    #     mock_run = Mock()
    #     mock.get_unused_sheets.return_value = [None, ] #just need one value
    #     self.assertGreater(len(mock.get_unused_sheets()), 0)
    #     self.assertIs(pr_fsevents.SampleSheet, mock)
    #     _run(pr_fsevents.register_new_run(mock_run))
    #     mock_run.save.assert_called()





# @patch('porerefiner.porerefiner.register_new_run', new_callable=AsyncMock)
# @patch('porerefiner.porerefiner.register_new_flowcell', new_callable=AsyncMock)
# @patch('porerefiner.porerefiner.Flowcell')
# @patch('porerefiner.porerefiner.Run')
# @patch('porerefiner.porerefiner.File')
# class TestPoreFSEventHander(TestCase):

#     class FakeEvent:
#         def __init__(self, path, is_dir=True):
#             self.src_path = path
#             self.is_directory = is_dir



#     @given(event=fsevents())
#     def test_on_created(self, event, *a, **k):
#         ut = porerefiner.PoreRefinerFSEventHandler(event.src_path.parent)
#         _run(ut.on_created(event))
#         assert True


#     #@skip('not implemented')

#     @given(flowcell_path=paths().filter(lambda p: isinstance(p, pathlib.Path)))
#     def test_on_created_flowcell(self, flowcell_path, *a, **k):
#         ut = porerefiner.PoreRefinerFSEventHandler(flowcell_path.parent)
#         event = self.FakeEvent(flowcell_path)
#         _run(ut.on_created(event))


#     def test_on_created_run_simple(self, path=pathlib.Path('/A/B/C/D/E'), *a, **k):
#         ut = porerefiner.PoreRefinerFSEventHandler(path.parent.parent)
#         event = self.FakeEvent(path)
#         _run(ut.on_created(event))


#     def test_on_created_run_deep(self, path=pathlib.Path('/A/B/C/D/E'), *a, **k):
#         ut = porerefiner.PoreRefinerFSEventHandler(path.parent.parent.parent)
#         event = self.FakeEvent(path)
#         _run(ut.on_created(event))



#     # @skip('not implemented')
#     # @with_database
#     @patch('porerefiner.porerefiner.Flowcell')
#     def test_on_created_file(self, mock_flow, path=pathlib.Path('/A/B/C/D/E'), *a, **k):
#         ut = porerefiner.PoreRefinerFSEventHandler(path.parent.parent.parent)
#         mock_flow.get_or_create.return_value = mock_run.get_or_create.return_value = (Mock(), False)
#         event = self.FakeEvent(rp(path), is_dir=False)
#         _run(ut.on_created(event))


#     def test_on_created_file_deep(self, path=pathlib.Path('/A/B/C/D/E'), *a, **k):
#         ut = porerefiner.PoreRefinerFSEventHandler(path.parent.parent.parent) #A/B
#         event = self.FakeEvent(path / 'test', is_dir=False) #E/test
#         _run(ut.on_created(event))


#     # @skip('not implemented')
#     @patch('porerefiner.porerefiner.File')
#     def test_on_modified(self, mock):
#         ut = porerefiner.PoreRefinerFSEventHandler(pathlib.Path('TEST'))
#         event = self.FakeEvent('TEST', False)
#         _run(ut.on_modified(event))
#         mock.get_or_none.assert_called()

#     @skip('not implemented')
#     @given(paths())
#     def test_on_deleted(self, path):
#         assert False


    # def setUp(self):
    #     super().setUp()
    #     self.flow = flow = models.Flowcell.create(consumable_id="TEST|TEST|TEST", consumable_type="TEST|TEST|TEST", path="TEST/TEST/TEST")
    #     self.run = models.Run.create(pk=RUN_PK, library_id='x', name=RUN_NAME, flowcell=flow, path="TEST/TEST/TEST")
    #     self.file = models.File.create(run=self.run, path='TEST/TEST/TEST/TEST', last_modified=datetime.now() - timedelta(hours=2))
    #     self.tag = models.Tag.create(name='TEST')
    #     models.TagJunction.create(tag=tag, run=self.run)

    # @skip('no test')
@mark.asyncio
@settings(deadline=500, suppress_health_check=(HealthCheck.all()))
@given(ss=Message.Samplesheets())
async def test_attach_sheet_run_no_run(db, ss):
    ut = rpc.PoreRefinerDispatchServer()
    strm = AsyncMock()
    strm.recv_message.return_value = messages.RunAttachRequest(sheet=ss)
    await ut.AttachSheetToRun(strm)
    strm.send_message.assert_called_once()



@mark.asyncio
@settings(deadline=500, suppress_health_check=(HealthCheck.all()))
@given(ss=Message.Samplesheets())
async def test_attach_sheet_to_run(ss, run):
    # self.flow = flow = models.Flowcell.create(consumable_id="TEST|TEST|TEST", consumable_type="TEST|TEST|TEST", path="TEST/TEST/TEST")
    ut = rpc.PoreRefinerDispatchServer()
    strm = AsyncMock()
    strm.recv_message.return_value = messages.RunAttachRequest(sheet=ss, id=run.id)
    await ut.AttachSheetToRun(strm)
    strm.send_message.assert_called_once()



#@skip('no test')
@patch('porerefiner.rpc.graceful_exit')
@patch('porerefiner.rpc.Server')
@mark.asyncio
async def test_start_server(mock, _):
    mock.return_value = coro = AsyncMock()
    await rpc.start_server(None)
    mock.assert_called()
    coro.start.assert_called()
    coro.wait_closed.assert_called()



def test_config_create_defaults():
    f = mktemp()
    c = config.Config(f)
    assert c.config
    os.unlink(f)

def test_config_dictlike_access():
    f = mktemp()
    c = config.Config(f)
    assert config.Config['server']['socket']

