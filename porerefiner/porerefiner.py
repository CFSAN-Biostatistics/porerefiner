# -*- coding: utf-8 -*-

"""Main module."""

from .config import config

import asyncio
import aiohttp
import daemon
import hachiko
import watchdog

from logging import log

log.getLogger('service')

def register_new_run(path): #TODO
    pass

def clean_up_run(run): #TODO
    pass

def get_run_info(run): #TODO
    pass

def attach_samplesheet_to_run(sheet, run=None): #TODO
    "Determine file format of sample sheet and load"
    pass

def list_runs(): #TODO
    pass

def poll_active_run(): #TODO
    "Scan run in progress, check for updated files, check for stale files, dispatch demultiplexing jobs"
    pass

def end_run(run): #TODO
    "Put run in closed status"


class PoreRefinerFSEventhandler(hachiko.hachiko.AIOEventHandler):

    def on_created(self, event):
        pass

    def on_modified(self, event):
        pass

def setup():
    "Initialize stuff"

def main(): #TODO
    "Main event loop and async"


if __name__ == '__main__':
    setup()
    with daemon.DaemonContext():
        main()
