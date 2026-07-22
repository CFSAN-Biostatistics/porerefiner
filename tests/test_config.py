"Tests for the Config loader."

import os
from tempfile import mktemp

from porerefiner import config


def test_config_creates_default_file():
    f = mktemp()
    try:
        c = config.Config(f)
        assert c.config
        assert os.path.exists(f)
        assert c.config['server']['socket']
    finally:
        if os.path.exists(f):
            os.unlink(f)
        config.Config.the_config = None  # reset singleton for other tests


def test_config_dictlike_access():
    f = mktemp()
    try:
        config.Config(f)
        assert config.Config['server']['socket']
    finally:
        if os.path.exists(f):
            os.unlink(f)
        config.Config.the_config = None


def test_new_config_file_client_only():
    f = mktemp()
    try:
        defaults = config.Config.new_config_file(f, client_only=True)
        assert 'server' in defaults
        # client-only config should not carry a database section
        assert 'database' not in defaults
    finally:
        if os.path.exists(f):
            os.unlink(f)


def test_new_config_file_server():
    f = mktemp()
    try:
        defaults = config.Config.new_config_file(f, client_only=False)
        assert defaults['database']['path']
        assert defaults['nanopore']['path']
        assert defaults['porerefiner']['run_polling_interval'] == 600
    finally:
        if os.path.exists(f):
            os.unlink(f)
