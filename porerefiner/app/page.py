from porerefiner.app import app
from porerefiner.cli_utils import server
from porerefiner.samplesheets import load_from_csv
from porerefiner.protocols.porerefiner.rpc.porerefiner_pb2 import RunRequest, RunListRequest, RunAttachRequest, RunRsyncRequest

from asyncio import run
from flask import render_template, current_app
import subprocess

from os import environ

async def list_run_runner():
    config = current_app.config['config_file']
    with server(config) as serv:
        return await serv.GetRuns(RunListRequest(all=True))

def list_runs():
    return run(list_run_runner()).runs.runs

@app.route('/attach')
@app.route('/api/form/attach')
def form():
    return render_template('submit.html', runs=list_runs(), hostname=current_app.config['host'])

@app.route('/')
@app.route('/view')
def runs():
    return render_template('view.html', runs=list_runs(), hostname=current_app.config['host'])

@app.route('/view/<int:run_id>')
def view_run(run_id):
    async def get_run(run_id):
        config = current_app.config['config_file']
        with server(config) as serv:
            return await serv.GetRunInfo(RunRequest(id=run_id))
    return render_template('run_view.html', run=run(get_run(run_id)).run)

@app.route('/template')
def template():
    return """porerefiner_ver,1.0.0
pool_id,
sequencing_kit,
sample_id,accession,barcode_id,organism,extraction_kit,comment,user
""", 200, {'Content-Type':'text/csv'}
