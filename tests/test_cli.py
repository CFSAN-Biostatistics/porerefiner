from tests import paths

from unittest import TestCase, skip
from unittest.mock import patch

from porerefiner import cli

class TestCli(TestCase):

    @skip("not sure how to test these")
    def test_ps(self, server=False, config=False, output_format=False, extend=False, _all=False, tags=[]):
        cli.ps(output_format, extend)
        assert False
