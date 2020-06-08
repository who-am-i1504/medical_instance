import logging
from flask_jsonschema import JsonSchema, ValidationError
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .constant import mysqllink

db = SQLAlchemy()
from .logger.log import Logger
# create and configure the app
app = Flask(__name__, instance_relative_config=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://' + mysqllink
app.config['SQLALCHEMY_POOL_SIZE'] = 10
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 15
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSONSCHEMA_DIR'] = os.path.join(app.root_path, 'schemas')
# if test_config is None:
#     # Load the instance config, if it exists, when not testing
#     app.config.from_pyfile('config.py', silent=True)
# else:
#     app.config.from_mapping(test_config)
db.init_app(app)
jsonschema = JsonSchema(app)
# log = Logger()
handler = logging.FileHandler('current.log', encoding='UTF-8')
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)s - %(message)s'))
app.logger.addHandler(handler)
log = app.logger
from .rule import hl7_rule, dicom_rule, astm_rule
from .collect import collect
from .monitor_rule import monitor
from .picture import download
import flask_back.helloworld as ap
app.register_blueprint(ap.bp)
app.register_blueprint(hl7_rule.bp)
app.register_blueprint(dicom_rule.bp)
app.register_blueprint(astm_rule.bp)
app.register_blueprint(monitor.bp)
app.register_blueprint(collect.bp)
app.register_blueprint(download.bp)
try:
    os.makedirs(app.instance_path)
except OSError:
    pass
