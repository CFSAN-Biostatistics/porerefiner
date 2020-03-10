from tests import paths

from unittest import TestCase
from unittest.mock import patch

from porerefiner import cli

class TestCli(TestCase):


    def test_ps(self, server=False, config=False, output_format=False, extend=False, _all=False, tags=False):
        cli.ps(config, output_format, extend, _all, tags)
        assert False
