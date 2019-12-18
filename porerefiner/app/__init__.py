from flask import Flask, request
app = Flask(__name__)

from . import main
from . import page
