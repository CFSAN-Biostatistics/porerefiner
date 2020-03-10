from flask import Flask, request
import os
from pathlib import Path
from subprocess import run

app = application = Flask(__name__)
app.config['config_file'] = os.environ.get('POREREFINER_CONFIG', Path.home() / '.porerefiner' / 'config.yaml')
app.config['host'] = os.environ.get('HOSTNAME', run(["hostname"], capture_output=True, text=True).stdout.strip())

from . import main
from . import page
