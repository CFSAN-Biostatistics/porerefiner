from tests import _run, fsevents

from unittest import TestCase
from unittest.mock import Mock, patch
from asyncmock import AsyncMock

from porerefiner.porerefiner import PoreRefinerFSEventHandler as Handler

from hypothesis import given
import hypothesis.strategies as strat

class TestPoreRefinerFSEventsHandler(TestCase):

    @patch('porerefiner.porerefiner.register_new_flowcell', new_callable=AsyncMock)
    @patch('porerefiner.porerefiner.Flowcell')
    @given(event=fsevents().filter(lambda e: e.is_directory))
    def test_on_created_flowcell(self, event, flow, reg):
        flow.get_or_create.return_value = (flow, True)
        _run(Handler(event.src_path.parent).on_created(event))
        reg.assert_called()


    @patch('porerefiner.porerefiner.register_new_run', new_callable=AsyncMock)
    @patch('porerefiner.porerefiner.Flowcell')
    @patch('porerefiner.porerefiner.Run')
    @given(event=fsevents().filter(lambda e: e.is_directory))
    def test_on_created_run(self, event, run, flow, reg):
        flow.get_or_create.return_value = (flow, False)
        run.get_or_create.return_value = (run, True)
        _run(Handler(event.src_path.parent.parent).on_created(event))
        reg.assert_called()

    @patch('porerefiner.porerefiner.Flowcell')
    @patch('porerefiner.porerefiner.Run')
    @patch('porerefiner.porerefiner.File')
    @given(event=fsevents().filter(lambda e: not e.is_dictionary))
    def test_on_created_file(self, event, file, run, flow):
        flow.get_or_create.return_value = run.get_or_create.return_value = (flow, False)
        _run(Handler(event.src_path.parent.parent.parent))
