# -*- coding: utf-8 -*-

"""Main module."""

import asyncio
import aiohttp
import click
import daemon
import datetime
import logging
import sys
import watchdog

from asyncio import run, gather, wait
from datetime import datetime, timedelta
from grpclib.server import Server
from grpclib.utils import graceful_exit
from hachiko.hachiko import AIOEventHandler, AIOWatchdog
from peewee import JOIN
from porerefiner import models
from porerefiner.models import Flowcell, Run, Qa, File, Job, SampleSheet, Sample, Tag, TagJunction
from porerefiner.cli_utils import relativize_path as r, absolutize_path as a
from porerefiner.jobs import poll_jobs
from os.path import split
from os import remove
from pathlib import Path

from porerefiner.protocols.minknow.rpc.manager_grpc import ManagerServiceStub
from porerefiner.protocols.porerefiner.rpc.porerefiner_pb2 import Run as RunMessage, RunList, RunResponse, Error, GenericResponse, RunRsyncResponse, RunListResponse
from porerefiner.protocols.porerefiner.rpc.porerefiner_grpc import PoreRefinerBase
from porerefiner.notifiers import NOTIFIERS

log = logging.getLogger('porerefiner.service')

def get_run(run_id):
    run = Run.get_or_none(Run.pk == run_id) or Run.get_or_none(Run.name == run_id) or Run.get_or_none(Run.alt_name == run_id)
    if not run:
        raise ValueError(f"Run id or name '{run_id}' not found.")
    return run

def make_run_msg(run):
    return RunMessage(id=run.pk,
                      name=run.name,
                      mnemonic_name=run.alt_name,
                      library_id=run.library_id,
                      status=run.status,
                      path=a(run.path),
                      flowcell_type=run.flowcell.consumable_type,
                      flowcell_id=run.flowcell.consumable_id,
                      basecalling_model=run.basecalling_model,
                      sequencing_kit=run.sample_sheet.sequencing_kit,
                      samples=[
                          RunMessage.Sample(id=sample.pk,
                                 name=sample.name,
                                 accession=sample.accession,
                                 barcode_id=sample.barcode_id,
                                 barcode_seq=sample.barcode_seq,
                                 organism=sample.organism,
                                 extraction_kit=sample.extraction_kit,
                                 comment=sample.comment,
                                 user=sample.user,
                                 files=[
                                    RunMessage.File(name=file.name,
                                         path=a(file.path),
                                         spot_id=None,
                                         size=0,
                                         ready=False,
                                         hash=file.checksum,
                                         tags=[tag.name for tag in file.tags])
                                 for file in sample.files],
                                 tags=[tag.name for tag in sample.tags]) for sample in run.samples],
                      files=[
                          RunMessage.File(name=file.name,
                               path=a(file.path),
                               spot_id=None,
                               size=0,
                               ready=False,
                               hash=file.checksum,
                               tags=[tag.name for tag in file.tags])
                      for file in run.files],
                      tags=[tag.name for tag in run.tags]
                      )

async def register_new_flowcell(path, nanopore_api=None): #TODO
    flow = Flowcell.create(path=path, consumable_id=path.name)

    if nanopore_api:
        #try to get some MinKnow stuff
        pass

async def register_new_run(path, nanopore_api=None): #TODO

    flow, _ = Flowcell.get_or_create(path=path.parent, consumable_id=path.parent.name)

    run = Run.create(path=path, status='RUNNING', flowcell=flow, name=path.name)

    if nanopore_api:
        #get minknow stuff if we can
        pass

    query = SampleSheet.get_unused_sheets()
    if query.count() == 1:
        #if there's an unattached sheet, attach it to this run
        sheet = next(query)
        run.sample_sheet = sheet
        run.save()

    return run



#Have to decide whether to keep this - we could just track FS events and clean up runs that way.
# async def clean_up_run(run_id):
#     def delete_file(file_records):
#         for file_record in file_records:
#             try:
#                 remove(a(file_record.path))
#             except OSError as e:
#                 if e.errno != 2:
#                     raise
#     run = get_run(run_id)
#     await asyncio.get_running_loop().run_in_executor(
#         None,
#         delete_file,
#         run.files
#     )
#     File.delete().where(File.run == run)
#     remove(a(run.path))
#     run.delete()




async def get_run_info(run_id):
    return make_run_msg(get_run(run_id))


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



async def list_runs(all=False, tags=[]):
    if tags:
        #implies all
        return [make_run_msg(run) for run in Run.select().join(TagJunction).join(Tag).where(Tag.name << tags)]
    if all:
        return [make_run_msg(run) for run in Run.select()]
    #only in-progress runs
    return [make_run_msg(run) for run in Run.select().where(Run.ended.is_null())]


async def poll_active_run():
    "Scan run(s) in progress, close out runs that have been stable for an hour"
    runs = Run.select().where(Run.status == 'RUNNING')
    i = 0
    for i, run in enumerate(runs, 1):
        if len(run.files) and all([datetime.now() - file.last_modified > timedelta(hours=1) for file in run.files]):
            await end_run(run)
    return i


async def end_run(run):
    "Put run in closed status"
    run.ended = datetime.now()
    run.status = 'DONE'
    run.save()
    tag, _ = Tag.get_or_create(name='finished')
    TagJunction.get_or_create(run=run, tag=tag)
    log.info(f"Run {run.alt_name} ended, no file modifications in the past hour")
    for notifier in NOTIFIERS:
        log.info(f"Firing notifier {notifier.name}")
        await notifier.notify(run, None, "Run finished")


async def send_run(run, dest): #TODO
    "Use RSYNC to send a run to a destination"
    pass


class PoreRefinerFSEventHandler(AIOEventHandler):
    "Eventhandler for file system events via Hachiko/Watchdog"

    def __init__(self, path):
        super().__init__()
        self.path = path

    async def on_created(self, event):
        "New flowcell folder, new run folder, or new file in run"
        log.info(f"Filesystem event: {event.src_path} created")
        if event.is_directory:
            path = Path(event.src_path)
            parent = path.parent
            if parent == Path(self.path):
                if not Flowcell.get_or_none(Flowcell.path == r(path)):
                    log.info("Registering new flowcell...")
                    await register_new_flowcell(r(path))
            else:
                if not Run.get_or_none(Run.path == r(path)):
                    log.info("Registering new run...")
                    await register_new_run(r(path))
        else:
            containing_folder, filename = split(event.src_path)
            run = Run.get(Run.path == r(containing_folder))
            log.info(f"New file found for run {run.alt_name}...")
            fi = File.get_or_create(run=run, path=r(event.src_path))

    async def on_modified(self, event):
        if not event.is_directory: #we don't care about directory modifications
            fi = File.get_or_none(File.path == r(event.src_path))
            if fi:
                fi.last_modified = datetime.now()
                fi.save()

    # async def on_deleted(self, event): #TODO
    #     "Update database if files are deleted."
    #     if event.is_directory:
    #         Run.delete().where(Run.path == r(event.src_path)).execute()
    #     else:
    #         File.delete().where(File.path == r(event.src_path)).execute()

class PoreRefinerDispatchServer(PoreRefinerBase):
    "Eventhandler for RPC events coming from command line or Flask app"

    async def GetRuns(self, stream: 'grpclib.server.Stream[porerefiner_pb2.RunListRequest, porerefiner_pb2.RunList]') -> None:
        log.info("API call: Get Runs")
        request = await stream.recv_message()
        log.debug(f"all:{request.all}, tags:{request.tags}")
        await stream.send_message(RunListResponse(runs=RunList(runs = await list_runs(request.all, request.tags))))
        log.info("Response sent")

    async def GetRunInfo(self, stream: 'grpclib.server.Stream[porerefiner_pb2.RunRequest, porerefiner_pb2.RunResponse]') -> None:
        request = await stream.recv_message()
        log.info(f"API call: get run info for run {request.id or request.name}")
        try:
            run_msg = await get_run_info(request.id or request.name)
            reply_msg = RunResponse(run=run_msg)
        except ValueError as e:
            err_msg = Error(type='ValueError', err_message=str(e))
            reply_msg = RunResponse(error=err_msg)
        await stream.send_message(reply_msg)
        log.info("Response sent")

    async def AttachSheetToRun(self, stream: 'grpclib.server.Stream[porerefiner_pb2.RunAttachRequest, porerefiner_pb2.RunAttachResponse]') -> None:
        request = await stream.recv_message()
        log.info("API call: Attach sample sheet")
        await stream.send_message(RunAttachResponse())
        log.info("Response sent")

    async def RsyncRunTo(self, stream: 'grpclib.server.Stream[porerefiner_pb2.RunRsyncRequest, porerefiner_pb2.RunRsyncResponse]') -> None:
        request = await stream.recv_message()
        log.info(f"API call: send run via rsync to {request.dest}")
        await stream.send_message(RunRsyncResponse())
        log.info("Response sent")

async def start_server(socket, *a, **k):
    "Coroutine to bring up the rpc server"
    server = Server([PoreRefinerDispatchServer()])
    with graceful_exit([server]):
        await server.start(path=str(socket))
        log.info(f"RPC server listening on {socket}...")
        await server.wait_closed()
        log.info(f"RPC server shutting down.")

async def start_fs_watchdog(path, *a, **k):
    "Coroutine to bring up the filesystem watchdog"
    watcher = AIOWatchdog(
        path,
        event_handler=PoreRefinerFSEventHandler(path)
        )
    watcher.start()
    log.info(f"Filesystem events being watched in {path}...")
    # watcher.wait_closed()
    # log.info(f"Filesystem event watcher shutting down.")

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
        po, su, co = await poll_jobs()
        log.info(f'{po} jobs polled, {su} submitted, {co} collected.')
        await asyncio.sleep(job_polling_interval) #poll every 30 minutes
        return asyncio.ensure_future(run_job_polling())
    return asyncio.ensure_future(run_job_polling())


async def serve(db_path=None, db_pragmas=None, wdog_settings=None, server_settings=None, system_settings=None):
    "Initialize and gather coroutines"
    if not all([db_path, db_pragmas, wdog_settings, server_settings, system_settings]): #need to defer loading config for testing purposes
        from porerefiner.config import config
        db_path=config['database']['path']
        db_pragmas=config['database']['pragmas']
        wdog_settings=config['nanopore']
        server_settings=config['server']
        system_settings=config['porerefiner']
    models._db.init(db_path, db_pragmas) # pragma: no cover
    [cls.create_table(safe=True) for cls in models.REGISTRY] # pragma: no cover
    try:
        results = await gather(start_server(**server_settings),
                    start_fs_watchdog(**wdog_settings),
                    start_run_end_polling(**system_settings),
                    start_job_polling(**system_settings))
    finally:
        log.info("Shutting down...")

async def shutdown(signal, loop):
    for task in asyncio.all_tasks():
        if task is not asyncio.current_task():
            task.cancel()

@click.command()
@click.option('-d', '--daemonize', 'demonize', default=False)
@click.option('-v', '--verbose', is_flag=True)
def main(verbose=False, demonize=False):
    "Start the main event loop"
    log = logging.getLogger('porerefiner')
    logging.basicConfig(stream=sys.stdout, level=(logging.INFO, logging.DEBUG)[verbose])

    if demonize:
        log.info("Starting daemon...")
        with daemon.DaemonContext():
            run(serve())
    else:
        log.info("Starting server...")
        run(serve())
    return 0



if __name__ == '__main__':
    sys.exit(main())                   # pragma: no cover
