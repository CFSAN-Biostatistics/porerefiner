from asyncio import run
from flask import Flask

import json


from porerefiner.cli_utils import server
from porerefiner.protocols.porerefiner.rpc.porerefiner_pb2 import RunRequest, RunListRequest, RunAttachRequest, RunRsyncRequest

app = Flask(__name__)




@app.route('/api/runs/<int:run_id>/attach', methods=['POST,'])
def attach_to_run(run_id):
    file = next(request.files.values())
    async def attach_runner(run_id, file):
        with server() as serv:
            return await serv.AttachSheetToRun(RunAttachRequest(file=file.read(), id=run_id))
    resp = run(attach_runner(run_id, file))
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

@app.route('/api/runs/<int:run_id>/send', methods=['POST'])
def send_run(run_id, dest): #TODO
    "Schedule a run to be sent via Rsync to the dest"
    pass

# @app.route('/api/runs/<int:run_id>', methods=['GET', 'POST', 'DELETE'])
# def run_control(run_id): #TODO
#     pass

@app.route('/api/runs/')
def list_runs():
    all = request.args.get('all', False)
    tags = [str(t) for t in request.args.get_list('tags')]
    async def list_run_runner(all, tags):
        with server() as serv:
            return await serv.GetRuns(RunListRequest(all=all, tags=tags))

    resp = run(list_run_runner(all, tags))
    return json.dumps(list(resp.runs.runs)), 200, {'ContentType':'application/json'}



