"Tests for cli_utils helpers and output formatters."

from pathlib import Path

import click
from pytest import mark, raises

from porerefiner import cli_utils
from porerefiner.cli_utils import (
    relativize_path,
    absolutize_path,
    ValidRunID,
    handle_connection_errors,
)


def test_relativize_absolutize_roundtrip():
    p = "/data/some/path"
    rel = relativize_path(p)
    assert isinstance(rel, Path)
    assert absolutize_path(rel) == p


def test_relativize_passthrough_non_str():
    # non-str, non-fspath values pass through unchanged
    assert relativize_path(5) == 5


def test_valid_run_id_int():
    conv = ValidRunID()
    assert conv.convert("42", None, None) == 42


def test_valid_run_id_str():
    conv = ValidRunID()
    assert conv.convert("my-run-name", None, None) == "my-run-name"


def test_handle_connection_errors_refused():
    @handle_connection_errors
    def boom():
        raise ConnectionRefusedError()

    with raises(SystemExit) as exc:
        boom()
    assert exc.value.code == 61


def test_handle_connection_errors_filenotfound():
    @handle_connection_errors
    def boom():
        e = FileNotFoundError()
        e.errno = 2
        raise e

    with raises(SystemExit) as exc:
        boom()
    assert exc.value.code == 2


def test_hr_formatter_smoke():
    # empty formatter should not raise
    with cli_utils.hr_formatter() as fmt:
        assert callable(fmt)


def test_json_formatter_smoke():
    with cli_utils.json_formatter() as fmt:
        assert callable(fmt)
