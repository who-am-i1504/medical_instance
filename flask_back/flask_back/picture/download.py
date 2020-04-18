from flask import (request, jsonify, Blueprint, render_template, make_response, send_from_directory, abort)
from flask_back import db, jsonschema, ValidationError, log
import os
import flask_back.constant as cnts

ALLOWED_EXTENSIONS=set(['png', 'jpg', 'JPG', 'PNG','gif', 'GIF'])

bp = Blueprint('picture_download', __name__, url_prefix='/picture')


basedir = os.path.abspath('upload')


@bp.route('/download/<string:pic_name>', methods=['GET'])
def download(pic_name):
    if request.method == 'GET':
        if os.path.isfile(os.path.join(basedir, pic_name)):
            return send_from_directory(basedir, pic_name, as_attachment=True)
        else:
            return '<h1>NOT FOUND</h1>'
    else:
        return '<h1>Wrong Request Function</h1>'

@bp.route('/show/<string:pic_name>', methods=['GET'])
def show(pic_name):
    if request.method == 'GET':
        if pic_name is None:
            return '<h1>Wrong Request Function</h1><h2>You didn\'t Input The Picture Path'
            pass
        else:
            image_data = open(os.path.join(basedir, '%s' % pic_name), 'rb').read()
            response = make_response(image_data)
            response.headers['Content-Type'] = 'image/png'
            return response
    else:
        return '<h1>Wrong Request Function</h1>'
        pass
