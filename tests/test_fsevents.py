from tests import fsevents, db


from unittest.mock import Mock, patch, AsyncMock

from pytest import mark

# from mock import AsyncMock
from tempfile import NamedTemporaryFile
from pathlib import Path

from porerefiner.fsevents import PoreRefinerFSEventHandler as Handler, end_file, end_run, register_new_run
from porerefiner.models import Run, Tag, TripleTag, File
from porerefiner.cli_utils import relativize_path as r

from hypothesis import given, settings, note
import hypothesis.strategies as strat





# @patch('porerefiner.fsevents.logging')
@given(event=fsevents(min_deep=4, isDirectory=True).filter(lambda e: len(e.src_path.parts) > 3)) #three levels deepl plus one
@mark.asyncio
async def test_on_created_run(db, event):
    with patch('porerefiner.fsevents.Run') as run:
        assert len(event.src_path.parts) > 2
        note(event.src_path)
        run.get_or_create.return_value = (run, True)
        await Handler(event.src_path.parts[0]).on_created(event)
        run.save.assert_called()

# # @skip("can't debug test")
# # @patch('porerefiner.fsevents.Flowcell')
# @mark.asyncio
# @settings(deadline=500)
@given(event=fsevents(min_deep=5, isDirectory=False).filter(lambda e: len(e.src_path.parts) > 4)) # run, plus one more for file
# @with_database
@mark.asyncio
async def test_on_created_file(db, event):
    with patch('porerefiner.fsevents.Run') as run:
        with patch('porerefiner.fsevents.File') as file:
            assert len(event.src_path.parts) > 3
            note(event.src_path)
            run.get_or_create.return_value = (run, False)
            await Handler(event.src_path.parts[0]).on_created(event)
            file.create.assert_called()

@mark.asyncio
@given(event=fsevents(min_deep=5, isDirectory=False).filter(lambda e: len(e.src_path.parts) > 4)) # run, plus one more for file
async def test_on_deleted_file(db, event):
    await Handler(event.src_path.parts[0]).on_created(event)
    fi = File.get_or_none(File.path == r(event.src_path))
    assert fi # check test setup correctly
    fi.tag("TEST")
    fi.ttag("TEST", "TEST", "TEST")
    await Handler(event.src_path.parts[0]).on_deleted(event)
    fi = File.get_or_none(File.path == r(event.src_path))
    assert fi is None # should be deleted

# class TestFSEventsPollingFunctions(TestCase):

#@given(file=files(real=True))
@mark.asyncio
async def test_end_file(file=Mock()):
    with NamedTemporaryFile(delete=False) as tfile:
        file.path = Path(tfile.name)
    await end_file(file)
    file.save.assert_called()
