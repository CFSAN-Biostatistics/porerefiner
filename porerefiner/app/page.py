from porerefiner.app import app
from porerefiner.cli_utils import server, load_from_csv
from porerefiner.protocols.porerefiner.rpc.porerefiner_pb2 import RunRequest, RunListRequest, RunAttachRequest, RunRsyncRequest

from asyncio import run
from flask import render_template
import subprocess

@app.route('/')
def index(): #TODO - make a webpage
    "Home view"
    pass

@app.route('/attach')
@app.route('/api/form/attach')
def form(): #TODO
    host = subprocess.run(['hostname'], stdout=subprocess.PIPE).stdout.split()
    async def list_run_runner():
        with server() as serv:
            return await serv.GetRuns(RunListRequest(all=True))

    resp = run(list_run_runner())
    return render_template('submit.html', runs=resp.runs, hostname=host)

@app.route('/template')
def template():
    return """porerefiner_ver,1.0.0
library_id,
sequencing_kit,
sample_id,accession,barcode_id,organism,extraction_kit,comment,user
""", 200, {'ContentType':'application/csv'}
