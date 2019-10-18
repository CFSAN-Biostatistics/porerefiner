# -*- coding: utf-8 -*-

"""Main module."""

import asyncio
import aiohttp
import daemon
import datetime

import logging
import watchdog

from grpclib.server import Server
from grpclib.utils import graceful_exit
from hachiko.hachiko import AIOEventHandler
from peewee import JOIN
from porerefiner.models import Run, QA, File, Job, SampleSheet, Sample
from porerefiner.cli_utils import relativize_path as r, absolutize_path as a
from os.path import split
from os import remove

from porerefiner.protocols.minknow.rpc.manager_grpc import ManagerServiceStub
from porerefiner.protocols.porerefiner.rpc.porerefiner_pb2 import Run as RunMessage, RunList, RunAttachResponse, RunRsyncResponse
from porerefiner.protocols.porerefiner.rpc.porerefiner_grpc import PoreRefinerBase

log = logging.getLogger('porerefiner.service')

def get_run(run_id):
    run = Run.get_or_none(Run.pk == run_id)
    if not run:
        run = Run.get_or_none(Run.human_name == run_id)
    if not run:
        raise ValueError(f"Run id or name '{run_id}' not found.")
    return run

async def register_new_run(path): #TODO

    run = Run(path=path, status='RUNNING')

    async with purerpc.insecure_channel(config['minknow_api']) as channel:
        client = ManagerStub(channel)
        reply = await client.DoSomething(path)

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
    return RunMessage(**vars(get_run(run_id)))

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



async def list_runs(): #TODO
    return [RunMessage(**vars(run)) async for run in Run.select()]

async def poll_active_run(): #TODO
    "Scan run in progress, check for updated files, check for stale files, dispatch demultiplexing jobs"
    pass

async def end_run(run): #TODO
    "Put run in closed status"
    pass

async def send_run(run, dest): #TODO
    "Use RSYNC to send a run to a destination"
    pass


class PoreRefinerFSEventHandler(AIOEventHandler):
    "Eventhandler for file system events via Hachiko/Watchdog"
    async def on_created(self, event):
        "New run folder, or new file in run"
        if event.is_directory:
            if not Run.get_or_none(Run.path == r(event.src_path)):
                await register_new_run(r(event.src_path))
        else:
            containing_folder, filename = split(event.src_path)
            run = Run.get(Run.path == r(containing_folder))
            fi = File.create(run=run, path=r(event.src_path))

    async def on_modified(self, event):
        if not event.is_directory: #we don't care about directory modifications
            fi = File.get_or_none(File.path == r(event.src_path))
            if fi:
                fi.last_modified = datetime.datetime.now()
                fi.save()

    async def on_deleted(self, event): #TODO
        "Update database if files are deleted."
        if event.is_dictionary:
            Run.delete().where(Run.path == r(event.src_path))
        else:
            File.delete().where(File.path == r(event.src_path))

class PoreRefinerDispatchServer(PoreRefinerBase):
    "Eventhandler for RPC events coming from command line or Flask app"

    async def GetRuns(self, stream: 'grpclib.server.Stream[porerefiner_pb2.RunListRequest, porerefiner_pb2.RunList]') -> None:
        request = await stream.recv_message()
        await stream.send_message(RunList(runs = await list_runs()))

    async def GetRunInfo(self, stream: 'grpclib.server.Stream[porerefiner_pb2.RunRequest, porerefiner_pb2.Run]') -> None:
        request = await stream.recv_message()
        await stream.send_message(await get_run_info(request.id or request.name))

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

async def start_fs_watchdog(nanopore_output_path, *a, **k):
    "Coroutine to bring up the filesystem watchdog"
    watcher = hachiko.hachiko.AIOWatchdog(nanopore_output_path, event_handler=PoreRefinerFSEventHandler())
    await watcher.start()
    log.info(f"Filesystem events being watched in {nanopore_output_path}...")
    await watcher.stop()
    log.info(f"Filesystem event watcher shutting down.")

def main():
    "Main event loop and async"
    from porerefiner.config import config
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(start_server(**config), start_fs_watchdog(**config)))


if __name__ == '__main__':
    with daemon.DaemonContext():
        main()
