from tests import _run, fsevents, files

from unittest import TestCase, skip
from unittest.mock import Mock, patch
from asyncmock import AsyncMock
from tempfile import NamedTemporaryFile

from porerefiner.fsevents import PoreRefinerFSEventHandler as Handler, end_file, end_run, register_new_run

from hypothesis import given
import hypothesis.strategies as strat

class TestPoreRefinerFSEventsHandler(TestCase):

    @skip('no flowcell support anymore')
    @patch('porerefiner.fsevents.register_new_flowcell', new_callable=AsyncMock)
    # @patch('porerefiner.fsevents.Flowcell')
    @given(event=fsevents().filter(lambda e: e.is_directory))
    def test_on_created_flowcell(self, event, reg):
        # flow.get_or_create.return_value = (flow, True)
        _run(Handler(event.src_path.parent).on_created(event))
        reg.assert_called()

    @patch('porerefiner.fsevents.register_new_run', new_callable=AsyncMock)
    # @patch('porerefiner.fsevents.Flowcell')
    @patch('porerefiner.fsevents.Run')
    @given(event=fsevents().filter(lambda e: e.is_directory))
    def test_on_created_run(self, event, run, reg):
        # flow.get_or_create.return_value = (flow, False)
        run.get_or_create.return_value = (run, True)
        _run(Handler(event.src_path.parent.parent).on_created(event))
        run.get_or_create.assert_called()

    # @patch('porerefiner.fsevents.Flowcell')
    @patch('porerefiner.fsevents.Run')
    @patch('porerefiner.fsevents.File')
    @given(event=fsevents().filter(lambda e: not e.is_directory))
    def test_on_created_file(self, event, file, run):
        run.get_or_create.return_value = (run, False)
        _run(Handler(event.src_path.parent.parent.parent).on_created(event))
        file.create.assert_called()

class TestFSEventsPollingFunctions(TestCase):

    #@given(file=files(real=True))
    def test_end_file(self, file=Mock()):
        with NamedTemporaryFile() as tfile:
            file.path = tfile.name
            _run(end_file(file))
            file.save.assert_called()
