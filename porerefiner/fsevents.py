import asyncio
import aiofile
import aiohttp
import click
import datetime
import hashlib
import json
import logging
import subprocess
import sys
import watchdog

from asyncio import run, gather, wait
from datetime import datetime, timedelta
from grpclib.server import Server
from grpclib.utils import graceful_exit
from hachiko.hachiko import AIOEventHandler, AIOWatchdog
from itertools import chain
from peewee import JOIN
from porerefiner import models
from porerefiner.models import Run, Qa, File, Job, SampleSheet, Sample, Tag, TagJunction
from porerefiner.cli_utils import relativize_path as r, absolutize_path as a, json_formatter
from porerefiner.jobs import poll_jobs, CLASS_REGISTRY, JOBS
from os.path import split, getmtime
from os import remove
from pathlib import Path

from porerefiner.protocols.minknow.rpc.manager_grpc import ManagerServiceStub
from porerefiner.protocols.porerefiner.rpc.porerefiner_pb2 import Run as RunMessage, RunList, RunResponse, Error, GenericResponse, RunRsyncResponse, RunListResponse
from porerefiner.protocols.porerefiner.rpc.porerefiner_grpc import PoreRefinerBase
from porerefiner.notifiers import NOTIFIERS

from porerefiner.rpc import get_run





log = logging.getLogger('porerefiner.fs')



async def register_new_flowcell(flow, nanopore_api=None):
    "Hook for new flowcells"
    log.info(f"Registering flowcell {flow.consumable_id}")
    if nanopore_api:
        pass

async def register_new_run(run, nanopore_api=None):
    "Hook for new runs"
    log.info(f"Registering run {run.name}")
    if nanopore_api:
        pass

    query = list(SampleSheet.get_unused_sheets()) #pre-fetch all
    if len(query) == 1:
        #if there's one unattached sheet, attach it to this run
        sheet = query[0]
        run.sample_sheet = sheet
        run.save()



async def attach_samplesheet_to_run(sheet, run_id=None):
    "Determine file format of sample sheet and load"
    if '.xls' in sheet:
        sheet = await SampleSheet.from_excel(sheet)
    else:
        sheet = await SampleSheet.from_csv(sheet)
    if run_id:
        # run = Run.get_or_none(Run.pk == run_id)
        # if not run:
        #     run = Run.get_or_none(Run.human_name == run_id)
        # if not run:
        #     raise ValueError(f"Run id or name '{run_id}' not found.")
        run = get_run(run_id)
        run.sample_sheet = sheet
        run.save()
    else:
        #find unassociated run
        query = Run.get_unannotated_runs()
        if query.count() == 1:
            run = next(query)
            run.sample_sheet = sheet
            run.save()
        else:
            raise ValueError("Run not specified and there are multiple runs in progress. Please specify a run by id, name, or nickname.")





async def poll_file(file):
    if datetime.now() - file.last_modified > timedelta(hours=1):
        await end_file(file)
        return True
    return False

async def poll_active_run():
    "Scan run(s) in progress, close out runs that have been stable for an hour"
    runs = Run.select().where(Run.status == 'RUNNING')
    i = 0
    for i, run in enumerate(runs, 1):
        if len(run.files) and all([await poll_file(file) for file in run.files]):
            await end_run(run)
    return i


async def end_run(run):
    "Put run in closed status"
    run.ended = datetime.now()
    run.status = 'DONE'
    run.save()
    run.tag('finished')
    log.info(f"Run {run.alt_name} ended, no file modifications in the past hour")
    for notifier in NOTIFIERS:
        log.info(f"Firing notifier {notifier.name}")
        await notifier.notify(run, None, "Run finished")
    for job in JOBS.RUNS:
        log.info(f"Scheduling job {type(job).__name__}")
        run.spawn(job)

async def end_file(file):
    "Put file in closed state"
    log.info(f"No recent modifications to {file.path}, scheduling analysis.")
    # try:
    #     proc = await asyncio.create_subprocess_shell(f'md5sum {file.path}', stdout=subprocess.PIPE)
    #     await proc.wait()
    #     return_val = await proc.stdout.readline()
    #     hash_val = return_val.split(b' ')[0]
    #     file.hash = hash_val
    #     file.save()
    # except (subprocess.CalledProcessError, ValueError) as e:
    #     log.error(e)
    async with aiofile.AIOFile(file.path, 'rb') as afile:
        ha = hashlib.md5()
        rdr = aiofile.Reader(afile, chunk_size=1024 * 1024)
        async for chunk in rdr:
            ha.update(chunk)
    file.hash = ha.hexdigest()
    file.save()
    for job in JOBS.FILES:
        log.info(f"Scheduling job {type(job).__name__} on {file.path}")
        file.spawn(job)


# async def send_run(run, dest):
#     "Use RSYNC to send a run to a destination"
#     pass


class PoreRefinerFSEventHandler(AIOEventHandler):
    "Eventhandler for file system events via Hachiko/Watchdog"

    def __init__(self, path, *a, **k):
        super().__init__(*a, **k)
        self.path = path


    async def on_created(self, event):
        """
        The all-important flowcell, run, and file detection hook.

        RULES: we're watching the nanopore output directory configured by config.

        A folder created under the output directory is an EXPERIMENT.

        A folder created under an experiment is a SAMPLE. We're ignoring both of these because the semantics don't map.

        A folder created under a SAMPLE is a RUN. This, we care about.

        A FILE created anywhere beneath a RUN directory is a file that is part of that run,
        as long as '_porerefiner' isn't part of the path.

        [EXPERIMENT_ID]/[SAMPLE_ID]/[START_TIME]_[DEVICE_ID]_[FLOWCELL_ID]_[SHORT_PROTOCOL_RUN_ID]


        """
        log.info(f"Filesystem event: {event.src_path} created")
        if '_porerefiner' not in str(event.src_path): #may need to exclude analysis results we create ourselves
            path = Path(event.src_path)
            rel = path.relative_to(self.path)
            # if len(rel.parts) >= 1: # not doing flowcells anymore
            #     rel_flow_path, *_ = rel.parts
            #     flow_path = self.path / Path(rel_flow_path)
            #     flow, new = Flowcell.get_or_create(path=r(flow_path), consumable_id=rel_flow_path)
            #     if new:
            #         await register_new_flowcell(flow)
            if len(rel.parts) >= 3:
                exp, sam, rel_run_path, *_ = rel.parts
                run_path = self.path / Path(exp) / Path(sam) / Path(rel_run_path)
                run, new = Run.get_or_create(path=r(run_path), name=rel_run_path)
                if new:
                    run.tag(exp)
                    run.tag(sam)
                    await register_new_run(run)
                    try:
                        st, dev_id, fc_id, prot_id = rel_run_path.split('_')
                        run.flowcell = fc_id
                        # run.tag(st)
                        run.tag(dev_id)
                        run.tag(prot_id)
                    except ValueError:
                        pass
                    run.save()
            if len(rel.parts) >=4 and not event.is_directory: #there's a file
                log.info(f"Registering new file {path} in {run.name}")
                f = File.create(run=run, path=path)
                f.tag(rel.parent.name)
                f.save()




    async def on_modified(self, event):
        if not event.is_directory: #we don't care about directory modifications
            fi = File.get_or_none(File.path == r(event.src_path))
            if not fi:
                await self.on_created(event)
            else:
                fi.last_modified = datetime.now()
                fi.save()

    # async def on_deleted(self, event): #TODO
    #     "Update database if files are deleted."
    #     if event.is_directory:
    #         Run.delete().where(Run.path == r(event.src_path)).execute()
    #     else:
    #         File.delete().where(File.path == r(event.src_path)).execute()


async def start_fs_watchdog(path, api=None, *a, **k):
    "Coroutine to bring up the filesystem watchdog"
    watcher = AIOWatchdog(
        path,
        event_handler=PoreRefinerFSEventHandler(path, *a, **k)
        )
    watcher.start()
    log.info(f"Filesystem events being watched in {path}...")
    # watcher.wait_closed()
    # log.info(f"Filesystem event watcher shutting down.")

async def in_progress_run_update(*args, **kwargs):
    "On server start, update all in-progress run files with last modified date."
    for run in Run.select().where(Run.status == 'RUNNING'):
        log.info(f"Checking in-progress run {run.name} for modifications")
        for file in run.all_files:
            file.last_modified = datetime.fromtimestamp(getmtime(a(file.path)))
            file.save()
            await asyncio.sleep(0)


async def start_run_end_polling(run_polling_interval, *a, **k):
    "Coro to bring up the run termination polling"
    log.info(f"Starting run polling...")
    async def run_end_polling():
        run_num = await poll_active_run()
        log.info(f"{run_num} runs polled.")
        await asyncio.sleep(run_polling_interval) #poll every ten minutes
        return asyncio.ensure_future(run_end_polling())
    return asyncio.ensure_future(run_end_polling())

async def start_job_polling(job_polling_interval, *a, **k):
    log.info(f'Starting job polling...')
    async def run_job_polling():
        po, su, co = await poll_jobs(
            Job.select().where(Job.status == 'READY'),
            Job.select().where(Job.status == 'RUNNING')
        )
        log.info(f'{po} jobs polled, {su} submitted, {co} collected.')
        await asyncio.sleep(job_polling_interval) #poll every 30 minutes
        return asyncio.ensure_future(run_job_polling())
    return asyncio.ensure_future(run_job_polling())
