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
from itertools import chain
from peewee import JOIN
from porerefiner import models
from porerefiner.models import Flowcell, Run, Qa, File, Job, SampleSheet, Sample, Tag, TagJunction
from porerefiner.cli_utils import relativize_path as r, absolutize_path as a
from porerefiner.jobs import poll_jobs, REGISTRY, JOBS, create_jobs_for_file, create_jobs_for_run
from os.path import split, getmtime
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
                    name=sample.sample_id,
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
                            size=0,
                            ready=False,
                            hash=file.checksum,
                            tags=[tag.name for tag in file.tags])
                    for file in sample.files],
                    tags=[tag.name for tag in sample.tags]
                    ) for sample in run.samples
        ],
        files=[
            RunMessage.File(name=file.name,
                path=a(file.path),
                size=0,
                ready=False,
                hash=file.checksum,
                tags=[tag.name for tag in file.tags])
        for file in run.files],
        tags=[tag.name for tag in run.tags]
        )

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
        #TODO
    await create_jobs_for_run(run)

async def end_file(file): #TODO
    "Put file in closed state"
    log.info(f"No recent modifications to {file.path}, scheduling analysis.")


# async def send_run(run, dest):
#     "Use RSYNC to send a run to a destination"
#     pass


class PoreRefinerFSEventHandler(AIOEventHandler):
    "Eventhandler for file system events via Hachiko/Watchdog"

    def __init__(self, path):
        super().__init__()
        self.path = path


    async def on_created(self, event):
        """
        The all-important flowcell, run, and file detection hook.

        RULES: we're watching the nanopore output directory configured by config.

        A folder created under the output directory is a FLOWCELL.

        A folder created under a flowcell is a RUN.

        A FILE created anywhere beneath a RUN directory is a file that is part of that run,
        as long as '_porerefiner' isn't part of the path.


        """
        log.info(f"Filesystem event: {event.src_path} created")
        if '_porerefiner' not in str(event.src_path): #may need to exclude analysis results we create ourselves
            path = Path(event.src_path)
            rel = path.relative_to(self.path)
            if len(rel.parts) >= 1:
                rel_flow_path, *_ = rel.parts
                flow_path = self.path / Path(rel_flow_path)
                flow, new = Flowcell.get_or_create(path=r(flow_path), consumable_id=rel_flow_path)
                if new:
                    await register_new_flowcell(flow)
            if len(rel.parts) >= 2:
                _, rel_run_path, *_ = rel.parts
                run_path = self.path / Path(rel_flow_path) / Path(rel_run_path)
                run, new = Run.get_or_create(flowcell=flow, path=r(run_path), name=rel_run_path)
                if new:
                    await register_new_run(run)
            if len(rel.parts) >=3 and not event.is_directory: #there's a file
                log.info(f"Registering new file {path} in {run.name}")
                File.create(run=run, path=path)




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
        try:
            run = get_run(request.id or request.name)
        except ValueError: #no run
            run = None
        ss = SampleSheet.new_sheet_from_message(request.sheet, run)
        await stream.send_message(GenericResponse())
        log.info("Response sent")

    async def RsyncRunTo(self, stream: 'grpclib.server.Stream[porerefiner_pb2.RunRsyncRequest, porerefiner_pb2.RunRsyncResponse]') -> None:
        request = await stream.recv_message()
        log.info(f"API call: send run via rsync to {request.dest}")
        await stream.send_message(RunRsyncResponse())
        log.info("Response sent")

    async def Tag(self, stream):
        request = await stream.recv_message()
        log.info(f"API call: tag run {request.id} with tags '{request.tags}'")
        run = Run.get_or_none(pk=request.id)
        resp = GenericResponse()
        if run:
            for tag in request.tags:
                if request.untag:
                    run.untag(tag)
                else:
                    run.tag(tag)
        else:
            resp.error = Error(type="NoSuchRun", err_message=f"run id {request.id} not found.")
        await stream.send_message(resp)
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

async def in_progress_run_update(*args, **kwargs):
    "On server start, update all in-progress run files with last modified date."
    for run in Run.select().where(Run.status == 'RUNNING'):
        for file in run.all_files:
            file.last_modified = datetime.fromtimestamp(getmtime(a(file.path)))
            file.save()
            await asyncio.sleep(0)


async def start_run_end_polling(run_polling_interval, *a, **k):
    "Coro to bring up the run termination polling"
    log.info(f"Starting run polling...")
    async def run_end_polling():
        await asyncio.sleep(run_polling_interval) #poll every ten minutes
        run_num = await poll_active_run()
        log.info(f"{run_num} runs polled.")
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
    models._db.init(db_path, db_pragmas)
    [cls.create_table(safe=True) for cls in models.REGISTRY]
    import porerefiner.jobs.submitters as submitters
    for submitter in submitters.SUBMITTERS:
        log.info(f'Running {type(submitter).__name__} integration no-op test')
        await submitter.test_noop()
    try:
        results = await gather(start_server(**server_settings),
                    start_fs_watchdog(**wdog_settings),
                    start_run_end_polling(**system_settings),
                    start_job_polling(**system_settings),
                    in_progress_run_update())
    finally:
        log.info("Shutting down...")

@click.group()
def cli():
    pass

@cli.command()
@click.option('-d', '--daemonize', 'demonize', is_flag=True, default=False)
@click.option('-v', '--verbose', is_flag=True)
def start(verbose=False, demonize=False):
    "Start the PoreRefiner service"
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

@cli.group()
def reset():
    "Utility function to reset various state."
    pass

@reset.command()
@click.argument('status', default="QUEUED", type=click.Choice([v for v, _ in Job.statuses], case_sensitive=True))
def jobs(status):
    "Reset all jobs to a particular status."
    if click.confirm(f"This will set all jobs to {status} status. Are you sure?"):
        click.echo("reset jobs")

@reset.command()
def runs():
    "Reset all runs to in-progress status."
    if click.confirm(f"This will set all runs to in-progress status, triggering notifiers and jobs in the next hour. Are you sure?"):
        click.echo("reset runs")

@reset.command()
def config():
    "Reset config to defaults."
    if click.confirm("This will reset your config to defaults. Are you sure?"):
        try:
            import importlib
            import porerefiner.config
            porerefiner.config.config_file.unlink()
            importlib.reload(porerefiner.config)
        except Exception:
            from os import environ
            config_file = Path(environ.get('POREREFINER_CONFIG', '/Users/justin.payne/.porerefiner/config.yml'))
            config_file.unlink()
            import porerefiner.config

@reset.command()
def database():
    "Reset database to empty state."
    if click.confirm("This will delete the porerefiner database. Are you sure?"):
        import porerefiner.config
        Path(porerefiner.config.config['database']['path']).unlink()

@reset.command()
def samplesheets():
    "Clear samplesheets that aren't attached to any run."
    click.echo("clear sheets")



if __name__ == '__main__':
    sys.exit(cli())                   # pragma: no cover
