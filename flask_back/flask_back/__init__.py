import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from flask_back.rule import hl7_rule, dicom_rule, http_rule
from flask_back.monitor_rule import monitor
import flask_back.app as ap

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://remote:beauty1234.@10.246.229.255:3306/medical'
    app.config['SQLALCHEMY_POOL_SIZE'] = 10
    app.config['SQLALCHEMY_POOL_TIMEOUT'] = 15
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # if test_config is None:
    #     # Load the instance config, if it exists, when not testing
    #     app.config.from_pyfile('config.py', silent=True)
    # else:
    #     app.config.from_mapping(test_config)
    db.init_app(app)
    app.register_blueprint(ap.bp)
    app.register_blueprint(hl7_rule.bp)
    app.register_blueprint(dicom_rule.bp)
    app.register_blueprint(monitor.bp)
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    return app