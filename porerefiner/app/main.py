from asyncio import run
from flask import Flask, request, current_app
from google.protobuf.json_format import MessageToJson

import json


from porerefiner.cli_utils import server
from porerefiner.samplesheets import load_from_csv
from porerefiner.protocols.porerefiner.rpc.porerefiner_pb2 import RunRequest, RunListRequest, RunAttachRequest, RunRsyncRequest

from porerefiner.app import app



@app.route('/api/form/attach/submit', methods=['POST', ])
@app.route('/api/runs/<int:run_id>/attach', methods=['POST,'])
def attach_to_run(run_id=None):
    if not run_id:
        run_id = request.form.get('run_id', None)
    file = request.files.get('sample_sheet')
    message = load_from_csv(file)
    async def attach_runner(run_id, message):
        with server(current_app.config['config_file']) as serv:
            return await serv.AttachSheetToRun(RunAttachRequest(name=run_id, sheet=message))
    resp = run(attach_runner(run_id, message))
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}



@app.route('/api/runs/<int:run_id>')
def get_run(run_id):
    "Get a single run"
    async def run_getter(run_id):
        with server(current_app.config['config_file']) as serv:
            return await serv.GetRunInfo(RunRequest(id = run_id))
    resp = run(run_getter(run_id))
    return MessageToJson(resp), 200, {'ContentType':'application/json'}

@app.route('/api/runs')
def list_runs():
    #all = request.args.get('all', False)
    tags = [str(t) for t in request.args.getlist('tags')]
    async def list_run_runner(all, tags):
        with server(current_app.config['config_file']) as serv:
            return await serv.GetRuns(RunListRequest(all=True, tags=tags))

    resp = run(list_run_runner(all, tags))
    return MessageToJson(resp), 200, {'ContentType':'application/json'}


