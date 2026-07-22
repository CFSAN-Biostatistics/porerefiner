from tests import paths

# from unittest import TestCase, skip
from unittest.mock import patch, AsyncMock

from pytest import mark

from porerefiner import cli
from click.testing import CliRunner



def help_runner(command):
    "Run the command with help flag and no arguments."
    runner = CliRunner()
    full_result = runner.invoke(command, ["--help"])
    assert full_result.exit_code == 0, "Non-zero exit code"

def test_ps_h(server=False, config=False, output_format=False, extend=False, _all=False, tags=[]):
    help_runner(cli.ps)

def test_info_h():
    help_runner(cli.info)

def test_template_h():
    help_runner(cli.template)

def test_tag_h():
    help_runner(cli.tag)

def test_untag_h():
    help_runner(cli.untag)

def test_load_h():
    help_runner(cli.load)

def test_test_plugins_h():
    help_runner(cli.test_plugins)




def ps(*args):
    runner = CliRunner()
    return runner.invoke(cli.ps, args)
    # self.assertEqual(result.exit_code, 0)

@patch("porerefiner.cli.server")
def test_ps_remote(mock):
    result = ps("-c", "localhost:8080")
    print(result.stdout)
    assert mock.called


@patch("porerefiner.cli.tag_runner", new_callable=AsyncMock)
def test_tag_invokes_runner(mock):
    "Regression: tag command had a broken signature (config/use_ssl mismatch)."
    runner = CliRunner()
    result = runner.invoke(cli.tag, ["5", "sometag"])
    assert result.exit_code == 0, result.output
    assert mock.called


@patch("porerefiner.cli.tag_runner", new_callable=AsyncMock)
def test_untag_invokes_runner(mock):
    "Regression: untag command had a broken signature."
    runner = CliRunner()
    result = runner.invoke(cli.untag, ["5", "sometag"])
    assert result.exit_code == 0, result.output
    assert mock.called
    _, kwargs = mock.call_args
    assert kwargs.get("untag") is True

