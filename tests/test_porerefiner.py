#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `porerefiner` package."""

from unittest import TestCase

from click.testing import CliRunner

from porerefiner import porerefiner
from porerefiner import cli

from hypothesis import given
import hypothesis.strategies as strat
from hypothesis_fspaths import fspaths


class TestCoreFunctions(TestCase):

    def setUp(self):
        pass


    def tearDown(self):
        pass

    @given(strat.one_of(strat.text(max_size=30), strat.integers()))
    def test_get_run(self, runid):
        pass

    @given(fspaths())
    def test_register_new_run(self, path):
        pass

    @given(strat.one_of(strat.text(max_size=30), strat.integers()))
    def test_get_run_info(self, run_id):
        pass

    def test_list_runs(self):
        pass

    def test_poll_active_run(self):
        pass

    def test_end_run(self):
        pass

    def test_send_run(self):
        pass



class TestPoreFSEventHander(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @given(fspaths())
    def test_on_created(self, path):
        pass

    @given(fspaths())
    def test_on_modified(self, path):
        pass

    @given(fspaths())
    def test_on_deleted(self, path):
        pass

class TestPoreDispatchServer(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_runs(self):
        pass

    def test_get_run_info(self):
        pass

    def test_attach_sheet_run(self):
        pass

    def test_rsync_run_to(self):
        pass

class TestServerStart(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_start_fs_watchdog(self):
        pass

    def test_start_server(self):
        pass
