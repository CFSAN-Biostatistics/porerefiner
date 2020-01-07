from flask import Flask, request
import os
from pathlib import Path

app = Flask(__name__)
app.config['config_file'] = os.environ.get('POREREFINER_CONFIG', Path.home() / '.porerefiner' / 'config.yaml')
app.config['host'] = os.environ['HOSTNAME']

from . import main
from . import page
