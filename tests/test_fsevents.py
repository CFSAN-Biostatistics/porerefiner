from tests import _run, fsevents, with_database

from unittest import TestCase, skip
from unittest.mock import Mock, patch, AsyncMock
# from mock import AsyncMock
from tempfile import NamedTemporaryFile

from porerefiner.fsevents import PoreRefinerFSEventHandler as Handler, end_file, end_run, register_new_run
from porerefiner.models import Run

from hypothesis import given, settings, note
import hypothesis.strategies as strat

class TestPoreRefinerFSEventsHandler(TestCase):

    @skip('no flowcell support anymore')
    # @patch('porerefiner.fsevents.register_new_flowcell', new_callable=AsyncMock)
    # @patch('porerefiner.fsevents.Flowcell')
    # @given(event=fsevents().filter(lambda e: e.is_directory))
    def test_on_created_flowcell(self, event, reg):
        # flow.get_or_create.return_value = (flow, True)
        _run(Handler(event.src_path.parent).on_created(event))
        reg.assert_called()

    # @skip("can't debug test")
    @patch('porerefiner.fsevents.logging')
    @given(event=fsevents(min_deep=4, isDirectory=True).filter(lambda e: len(e.src_path.parts) > 3)) #three levels deepl plus one
    @with_database
    def test_on_created_run(self, log, event):
        with patch('porerefiner.fsevents.Run') as run:
            self.assertGreater(len(event.src_path.parts), 2)
            note(event.src_path)
            run.get_or_create.return_value = (run, True)
            _run(Handler(event.src_path.parts[0]).on_created(event))
            run.save.assert_called()

    # @skip("can't debug test")
    # @patch('porerefiner.fsevents.Flowcell')
    @settings(deadline=500)
    @given(event=fsevents(min_deep=5, isDirectory=False).filter(lambda e: len(e.src_path.parts) > 4)) # run, plus one more for file
    @with_database
    def test_on_created_file(self, event):
        with patch('porerefiner.fsevents.Run') as run:
            with patch('porerefiner.fsevents.File') as file:
                self.assertGreater(len(event.src_path.parts), 3)
                note(event.src_path)
                run.get_or_create.return_value = (run, False)
                _run(Handler(event.src_path.parts[0]).on_created(event))
                file.create.assert_called()

class TestFSEventsPollingFunctions(TestCase):

    #@given(file=files(real=True))
    def test_end_file(self, file=Mock()):
        with NamedTemporaryFile() as tfile:
            file.path = tfile.name
            _run(end_file(file))
            file.save.assert_called()
