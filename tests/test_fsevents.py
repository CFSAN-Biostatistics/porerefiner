from tests import _run, fsevents, files

from unittest import TestCase, skip
from unittest.mock import Mock, patch
from mock import AsyncMock
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

    @skip("can't debug test")
    @given(event=fsevents().filter(lambda e: e.is_directory))
    def test_on_created_run(self, event):
        with patch('porerefiner.fsevents.register_new_run', new_callable=AsyncMock) as reg:
            with patch('porerefiner.fsevents.Run') as run:
                #self.assertEqual(len(event.src_path.parts), 3)
                run.get_or_create.return_value = (run, True)
                _run(Handler(event.src_path.parent.parent.parent).on_created(event))
                run.save.assert_called()

    @skip("can't debug test")
    # @patch('porerefiner.fsevents.Flowcell')
    @given(event=fsevents().filter(lambda e: not e.is_directory))
    def test_on_created_file(self, event):
        with patch('porerefiner.fsevents.Run') as run:
            with patch('porerefiner.fsevents.File') as file:
                run.get_or_create.return_value = (run, False)
                _run(Handler(event.src_path.parent.parent.parent.parent).on_created(event))
                file.create.assert_called()

class TestFSEventsPollingFunctions(TestCase):

    #@given(file=files(real=True))
    def test_end_file(self, file=Mock()):
        with NamedTemporaryFile() as tfile:
            file.path = tfile.name
            _run(end_file(file))
            file.save.assert_called()
