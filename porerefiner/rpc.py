import asyncio
import aiohttp
import click
import datetime
import json
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



log = logging.getLogger('porerefiner.rpc')


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
        # flowcell_type=run.flowcell.consumable_type,
        # flowcell_id=run.flowcell.consumable_id,
        basecalling_model=run.basecalling_model,
        sequencing_kit=run.sample_sheet.barcoding_kit,
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
                            size=file.path.stat().st_size,
                            ready=datetime.now() - file.last_modified > timedelta(hours=1),
                            hash=file.checksum,
                            tags=[tag.name for tag in file.tags])
                    for file in sample.files],
                    tags=[tag.name for tag in sample.tags]
                    ) for sample in run.samples
        ],
        files=[
            RunMessage.File(name=file.name,
                path=a(file.path),
                size=file.path.stat().st_size,
                ready=datetime.now() - file.last_modified > timedelta(hours=1),
                hash=file.checksum,
                tags=[tag.name for tag in file.tags])
        for file in run.files],
        tags=[tag.name for tag in run.tags]
        )

async def get_run_info(run_id):
    return make_run_msg(get_run(run_id))

async def list_runs(all=False, tags=[]):
    if tags:
        #implies all
        return [make_run_msg(run) for run in Run.select().join(TagJunction).join(Tag).where(Tag.name << tags)]
    if all:
        return [make_run_msg(run) for run in Run.select()]
    #only in-progress runs
    return [make_run_msg(run) for run in Run.select().where(Run.ended.is_null())]




class PoreRefinerDispatchServer(PoreRefinerBase):
    "Eventhandler for RPC events coming from command line or Flask app"

    async def GetRuns(self, stream: 'grpclib.server.Stream[porerefiner_pb2.RunListRequest, porerefiner_pb2.RunList]') -> None:
        log.debug("API call: Get Runs")
        request = await stream.recv_message()
        log.debug(f"all:{request.all}, tags:{request.tags}")
        await stream.send_message(RunListResponse(runs=RunList(runs = await list_runs(request.all, request.tags))))
        log.debug("Response sent")

    async def GetRunInfo(self, stream: 'grpclib.server.Stream[porerefiner_pb2.RunRequest, porerefiner_pb2.RunResponse]') -> None:
        request = await stream.recv_message()
        log.debug(f"API call: get run info for run {request.id or request.name}")
        try:
            run_msg = await get_run_info(request.id or request.name)
            reply_msg = RunResponse(run=run_msg)
        except ValueError as e:
            err_msg = Error(type='ValueError', err_message=str(e))
            reply_msg = RunResponse(error=err_msg)
        await stream.send_message(reply_msg)
        log.debug("Response sent")

    async def AttachSheetToRun(self, stream: 'grpclib.server.Stream[porerefiner_pb2.RunAttachRequest, porerefiner_pb2.RunAttachResponse]') -> None:
        request = await stream.recv_message()
        log.debug("API call: Attach sample sheet")
        run = None
        try:
            run = get_run(request.id or request.name)
        except ValueError: #no run
            query = Run.get_unannotated_runs()
            if query.count() == 1:
                run = next(query)
        ss = SampleSheet.new_sheet_from_message(request.sheet, run)
        await stream.send_message(GenericResponse())
        log.debug("Response sent")

    async def RsyncRunTo(self, stream: 'grpclib.server.Stream[porerefiner_pb2.RunRsyncRequest, porerefiner_pb2.RunRsyncResponse]') -> None:
        request = await stream.recv_message()
        log.debug(f"API call: send run via rsync to {request.dest}")
        await stream.send_message(RunRsyncResponse())
        log.debug("Response sent")

    async def Tag(self, stream):
        request = await stream.recv_message()
        log.debug(f"API call: tag run {request.id} with tags '{request.tags}'")
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
        log.warning(f"RPC server shutting down.")


