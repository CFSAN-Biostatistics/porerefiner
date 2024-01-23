# -*- coding: utf-8 -*-

"""Top-level package for PoreRefiner."""

__author__ = """Justin Payne"""
__email__ = 'justin.payne@fda.hhs.gov'

# import porerefiner.porerefiner

import logging
from importlib.metadata import entry_points

log = logging.getLogger("porerefiner.plugins")

# Load plugins, if any
# do this last
discovered_plugins = entry_points(group='porerefiner.plugins')
for module in discovered_plugins:
    try:
        module.load()
    except Exception as e:
        log.error(e)