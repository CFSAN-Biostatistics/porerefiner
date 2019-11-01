# -*- coding: utf-8 -*-

"""Main module."""

import asyncio
import aiohttp
import daemon
import datetime

import logging
import watchdog

from datetime import datetime, timedelta
from grpclib.server import Server
from grpclib.utils import graceful_exit
from hachiko.hachiko import AIOEventHandler
from peewee import JOIN
from porerefiner import models
from porerefiner.models import Flowcell, Run, Qa, File, Job, SampleSheet, Sample, Tag, TagJunction
from porerefiner.cli_utils import relativize_path as r, absolutize_path as a
from porerefiner.jobs import poll_jobs
from os.path import split
from os import remove
from pathlib import Path

from porerefiner.protocols.minknow.rpc.manager_grpc import ManagerServiceStub
from porerefiner.protocols.porerefiner.rpc.porerefiner_pb2 import Run as RunMessage, RunList, RunResponse, Error, RunAttachResponse, RunRsyncResponse
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
                          Sample(id=sample.pk,
                                 name=sample.name,
                                 accession=sample.accession,
                                 barcode_id=sample.barcode_id,
                                 barcode_seq=sample.barcode_seq,
                                 organism=sample.organism,
                                 extraction_kit=sample.extraction_kit,
                                 comment=sample.comment,
                                 user=sample.user,
                                 files=[
                                    File(name=file.name,
                                         path=a(file.path),
                                         spot_id=None,
                                         size=0,
                                         ready=False,
                                         tags=[tag.name for tag in file.tags])
                                 for file in sample.files],
                                 tags=[tag.name for tag in sample.tags]) for sample in run.samples],
                      tags=[tag.name for tag in run.tags]
                      )

async def register_new_flowcell(path): #TODO
    pass

async def register_new_run(path): #TODO

    run = Run(path=path, status='RUNNING')

    #async with glibrpc.utils.insecure_channel(config['minknow_api']) as channel:
    #    client = ManagerStub(channel)
        # reply = await client.DoSomething(path)

    #somehow need to link to the correct run - is it just the current run in progress?

    run.library_id = reply.LibraryID #probably doesn't work
    run.flowcell_type = reply.FlowcellType
    run.flowcell_id = reply.FlowcellID
    run.basecalling_model = reply.BasecallingModel

    run.save()

    query = SampleSheet.select().where(SampleSheet.run == None)
    if query.count() == 1:
        #if there's an unattached sheet, attach it to this run
        sheet = query.next()
        sheet.run = run
        sheet.save()



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
        sheet.run = get_run(run_id)
    else:
        #find unassociated run
        query = Run.query().join(SampleSheet, JOIN.OUTER_JOIN).where(SampleSheet.pk == None, Run.status == 'RUNNING')
        if query.count() == 1:
            sheet.run = query.next()
    sheet.save()



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
    runs = list(Run.select(Run.ended.is_null(False)))
    for run in runs:
        if all([datetime.now() - file.last_modified > timedelta(hours=1) for file in run.files]):
            await end_run(run)
    return len(runs)


async def end_run(run): #TODO
    "Put run in closed status"
    run.ended = datetime.now()
    for notifier in NOTIFIERS:
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
        if event.is_directory:
            path = Path(event.src_path)
            parent = path.parent
            if parent == Path(self.path):
                if not Flowcell.get_or_none(Flowcell.path == r(path)):
                    await register_new_flowcell(r(path))
            else:
                if not Run.get_or_none(Run.path == r(path)):
                    await register_new_run(r(path))
        else:
            containing_folder, filename = split(event.src_path)
            run = Run.get(Run.path == r(containing_folder))
            fi = File.get_or_create(run=run, path=r(event.src_path))

    async def on_modified(self, event):
        if not event.is_directory: #we don't care about directory modifications
            fi = File.get_or_none(File.path == r(event.src_path))
            if fi:
                fi.last_modified = datetime.now()
                fi.save()

    async def on_deleted(self, event): #TODO
        "Update database if files are deleted."
        if event.is_dictionary:
            Run.delete().where(Run.path == r(event.src_path)).execute()
        else:
            File.delete().where(File.path == r(event.src_path)).execute()

class PoreRefinerDispatchServer(PoreRefinerBase):
    "Eventhandler for RPC events coming from command line or Flask app"

    async def GetRuns(self, stream: 'grpclib.server.Stream[porerefiner_pb2.RunListRequest, porerefiner_pb2.RunList]') -> None:
        request = await stream.recv_message()
        await stream.send_message(RunList(runs = await list_runs(request.all, request.tags)))

    async def GetRunInfo(self, stream: 'grpclib.server.Stream[porerefiner_pb2.RunRequest, porerefiner_pb2.RunResponse]') -> None:
        request = await stream.recv_message()
        try:
            run_msg = await get_run_info(request.id or request.name)
            reply_msg = RunResponse(run=run_msg)
        except ValueError as e:
            err_msg = Error(type='ValueError', err_message=e.message)
            reply_msg = RunResponse(error=err_msg)
        return await stream.send_message(reply_msg)

    async def AttachSheetToRun(self, stream: 'grpclib.server.Stream[porerefiner_pb2.RunAttachRequest, porerefiner_pb2.RunAttachResponse]') -> None:
        request = await stream.recv_message()

        await stream.send_message(RunAttachResponse())

    async def RsyncRunTo(self, stream: 'grpclib.server.Stream[porerefiner_pb2.RunRsyncRequest, porerefiner_pb2.RunRsyncResponse]') -> None:
        request = await stream.recv_message()

        await stream.send_message(RunRsyncResponse())

async def start_server(socket, *a, **k):
    "Coroutine to bring up the rpc server"
    server = Server([PoreRefinerDispatchServer()])
    with graceful_exit([server]):
        await server.start(socket)
        log.info(f"RPC server listening on {socket}...")
        await server.wait_closed()
        log.info(f"RPC server shutting down.")

async def start_fs_watchdog(path, *a, **k):
    "Coroutine to bring up the filesystem watchdog"
    watcher = hachiko.hachiko.AIOWatchdog(
        path,
        event_handler=PoreRefinerFSEventHandler(path)
        )
    await watcher.start()
    log.info(f"Filesystem events being watched in {path}...")
    await watcher.wait_closed()
    log.info(f"Filesystem event watcher shutting down.")

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


def main(db_path=None, db_pragmas=None, wdog_settings=None, server_settings=None, system_settings=None):
    "Main event loop and async"
    if not all(db_path, db_pragmas, wdog_settings, server_settings, system_settings): #need to defer loading config for testing purposes
        from porerefiner.config import config
        db_path=config['database']['path']
        db_pragmas=config['database']['pragmas']
        wdog_settings=config['nanopore']
        server_settings=config['server']
        system_settings=config['porerefiner']
    models._db.init(db_path, db_pragmas) # pragma: no cover
    [cls.create_table(safe=True) for cls in models.REGISTRY] # pragma: no cover

    asyncio.run(asyncio.gather(start_server(**server_settings),
                               start_fs_watchdog(**wdog_settings),
                               start_run_end_polling(**system_settings),
                               start_job_polling(**system_settings),
                               return_exceptions=True)) #pragma: no cover

async def shutdown(signal, loop):
    for task in asyncio.all_tasks():
        if task is not asyncio.current_task():
            task.cancel()


if __name__ == '__main__':
    with daemon.DaemonContext():  # pragma: no cover
        main()                    # pragma: no cover
