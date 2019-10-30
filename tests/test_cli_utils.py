

from hypothesis import given
import hypothesis.strategies as strat
# from hypothesis_fspaths import fspaths

from unittest import TestCase, skip

from tests import paths, TestBase

from pathlib import Path

class TestUtilities(TestBase):

    @given(path=paths())
    def test_inverse_ops(self, path):
        from porerefiner.cli_utils import relativize_path, absolutize_path
        self.assertEqual(absolutize_path(relativize_path(path)), relativize_path(absolutize_path(path)))

    @skip("no test yet")
    def test_server(self):
        pass

    @skip("no test yet")
    def test_human_readable_formatter(self, **k):
        pass

    @skip("no test yet")
    def test_json_formatter(self, **k):
        pass

    @skip("no test yet")
    def test_xml_formatter(self, **k):
        pass
