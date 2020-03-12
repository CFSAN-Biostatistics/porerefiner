from unittest import TestCase, skip
from unittest.mock import patch, Mock, MagicMock
from mock import AsyncMock

from tests import paths, with_database, TestBase

from porerefiner.app.main import app as _app
from porerefiner.cli_utils import server




class TestFlask(TestCase):

    def setUp(self):
        global app
        app = _app.test_client()


    @skip("can't mock")
    @patch('porerefiner.app.main.server')
    def test_attach_run(self, mock):
        mock.__enter__ = mock
        mock.__exit__ = mock
        app.post('/api/runs/1/attach')
        mock.AttachSheetToRun.assert_called_once()

    @skip("can't mock")
    @patch('porerefiner.app.main.server')
    def test_list_runs(self, mock):
        mock.return_value.__enter__.return_value = m = AsyncMock(__iter__=Mock())
        #mock.return_value.__exit__ = mock
        app.get('/api/runs/')
