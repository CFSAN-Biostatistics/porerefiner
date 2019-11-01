

from hypothesis import given
import hypothesis.strategies as strat
# from hypothesis_fspaths import fspaths

from unittest import TestCase, skip
from unittest.mock import patch

from tests import paths, TestBase

from pathlib import Path

from porerefiner import cli_utils

class TestUtilities(TestCase):

    @skip('unclear goal')
    @given(path=paths())
    def test_inverse_ops(self, path):
        from porerefiner.cli_utils import relativize_path, absolutize_path
        self.assertEqual(absolutize_path(relativize_path(path)), relativize_path(absolutize_path(path)))

    @skip("no test yet")
    @patch('porerefiner.cli_utils.Channel')
    @patch('porerefiner.config.config')
    def test_server(self, mock_conf, mock_chan):
        from porerefiner.protocols.porerefiner.rpc.porerefiner_grpc import PoreRefinerStub
        with cli_utils.server() as serv:
            self.assertIsInstance(serv, PoreRefinerStub)
            mock_chan.assert_called()
        mock_chan.closed.assert_called()

    @skip("no test yet")
    def test_human_readable_formatter(self, **k):
        pass

    @skip("no test yet")
    def test_json_formatter(self, **k):
        pass

    @skip("no test yet")
    def test_xml_formatter(self, **k):
        pass
