from tests import paths

from unittest import TestCase, skip
from unittest.mock import patch

from porerefiner import cli
from click.testing import CliRunner

class TestCli(TestCase):

    def help_runner(self, command):
        "Run the command with help flag and no arguments."
        runner = CliRunner()
        full_result = runner.invoke(command, ["--help"])
        self.assertEqual(full_result.exit_code, 0)

    def test_ps_h(self, server=False, config=False, output_format=False, extend=False, _all=False, tags=[]):
        self.help_runner(cli.ps)

    def test_info_h(self):
        self.help_runner(cli.info)

    def test_template_h(self):
        self.help_runner(cli.template)

    def test_tag_h(self):
        self.help_runner(cli.tag)

    def test_untag_h(self):
        self.help_runner(cli.untag)

    def test_load_h(self):
        self.help_runner(cli.load)

    def test_test_plugins_h(self):
       self.help_runner(cli.test_plugins)
