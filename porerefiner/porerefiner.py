# -*- coding: utf-8 -*-

"""Main module."""

from .config import config

import asyncio
import aiohttp
import daemon
import datetime
import hachiko
import purerpc
import watchdog

from logging import log
from porerefiner.models import Run, QA, File, Job, SampleSheet, Sample
from porerefiner.cli_utils import relativize_path as r, absolutize_path as a
from os.path import split

from porerefiner.minknow_api.minknow.rpc.manager_pb2 import ManagerStub #probably not right

log.getLogger('service')


async def register_new_run(path): #TODO

    run = Run(path=path, status='RUNNING')

    async with purerpc.insecure_channel(config['minknow_api']) as channel:
        client = ManagerStub(channel)
        reply = await client.DoSomething(path)

    run.library_id = reply.LibraryID #probably doesn't work
    run.flowcell_type = reply.FlowcellType
    run.flowcell_id = reply.FlowcellID
    run.basecalling_model = reply.BasecallingModel

    run.save()




async def clean_up_run(run): #TODO
    pass

async def get_run_info(run_id): #TODO
    run = Run.get_or_none(Run.pk == run_id)
    if not run:
        run = Run.get_or_none(Run.human_name == run_id)
    if not run:
        raise ValueError(f"Run id or name '{run_id}' not found.")
    return run.to_json()

async def attach_samplesheet_to_run(sheet, run=None): #TODO
    "Determine file format of sample sheet and load"
    pass

async def list_runs(): #TODO
    return [run.to_json() for run in Run.select()]

async def poll_active_run(): #TODO
    "Scan run in progress, check for updated files, check for stale files, dispatch demultiplexing jobs"
    pass

async def end_run(run): #TODO
    "Put run in closed status"
    pass


class PoreRefinerFSEventhandler(hachiko.hachiko.AIOEventHandler):

    async def on_created(self, event):
        "New run folder, or new file in run"
        if event.is_directory:
            if not Run.get_or_none(Run.path == r(event.src_path)):
                await register_new_run(r(event.src_path))
        else:
            containing_folder, filename = split(event.src_path)
            run = Run.get(Run.path == r(containing_folder))
            fi = File.create(run=run, path=r(event.src_path))

    def on_modified(self, event):
        if not event.is_directory: #we don't care about directory modifications
            fi = File.get_or_none(File.path == r(event.src_path))
            if fi:
                fi.last_modified = datetime.datetime.now()
                fi.save()

def setup():
    "Initialize stuff"

def main(): #TODO
    "Main event loop and async"


if __name__ == '__main__':
    setup()
    with daemon.DaemonContext():
        main()
