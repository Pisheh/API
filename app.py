from flask import *
from mongoengine import *

from api import api_blueprint
from model import *

app = Flask(__name__)
app.register_blueprint(api_blueprint)