from flask import (request, jsonify, Blueprint, render_template, make_response, send_from_directory, abort)
from flask_back import db, jsonschema, ValidationError, log
import os
import flask_back.constant as cnts
from flask_back.constant import PicturePath
import redis
from flask_back.user.user import reids_pool

# ALLOWED_EXTENSIONS=set(['png', 'jpg', 'JPG', 'PNG','gif', 'GIF'])

bp = Blueprint('picture_download', __name__, url_prefix='/picture')

# @bp.before_request
# def validSession():
#     back = {
#         "status":cnts.quit_login,
#         "message":cnts.quit_login_message,
#         "data":{}
#     }
#     session=redis.Redis(connection_pool=reids_pool)
#     if 'X-Token' in request.headers.keys():
#         sessionid = request.headers['X-Token']
#         if session.exists(sessionid):
#             if cnts.validReader(session.hget(sessionid, 'authority')):
#                 back['message'] = '您的权限不足'
#                 return jsonify(back)
#             return None
#     return jsonify(back)

@bp.route('/download/<string:pic_name>', methods=['GET'])
def download_one(pic_name):
    if request.method == 'GET':
        if os.path.exists(os.path.join(PicturePath, pic_name)):
            return send_from_directory(os.path.join(os.getcwd(), PicturePath), pic_name, as_attachment=True)
        else:
            return '<h1>NOT FOUND</h1>'
    else:
        return '<h1>Wrong Request Function</h1>'

@bp.route('/show/<string:pic_name>', methods=['GET'])
def show_one(pic_name):
    if request.method == 'GET':
        if pic_name is None:
            return '<h1>Wrong Request Function</h1><h2>You didn\'t Input The Picture Path'
            pass
        else:
            if not os.path.exists(os.path.join(PicturePath, '%s' % pic_name)):
                return '<h1>NOT FOUND</h1>'
            image_data = open(os.path.join(PicturePath, '%s' % pic_name), 'rb').read()
            response = make_response(image_data)
            response.headers['Content-Type'] = 'image/png'
            return response
    else:
        return '<h1>Wrong Request Function</h1>'
        pass



@bp.route('/download/<string:pic_name>/<string:pic>', methods=['GET'])
def download(pic_name,pic):
    if request.method == 'GET':
        if pic is not None and not pic == '':
                pic_name = os.path.join(pic_name, pic)
        if os.path.exists(os.path.join(PicturePath, pic_name)):
            return send_from_directory(os.path.join(os.getcwd(), PicturePath), pic_name, as_attachment=True)
        else:
            return '<h1>NOT FOUND</h1>'
    else:
        return '<h1>Wrong Request Function</h1>'

@bp.route('/show/<string:pic_name>/<string:pic>', methods=['GET'])
def show(pic_name,pic):
    if request.method == 'GET':
        if pic_name is None:
            return '<h1>Wrong Request Function</h1><h2>You didn\'t Input The Picture Path'
            pass
        else:
            if pic is not None and not pic == '':
                pic_name = os.path.join(pic_name, pic)
            if not os.path.exists(os.path.join(PicturePath, '%s' % pic_name)):
                return '<h1>NOT FOUND</h1>'
            image_data = open(os.path.join(PicturePath, '%s' % pic_name), 'rb').read()
            response = make_response(image_data)
            response.headers['Content-Type'] = 'image/png'
            return response
    else:
        return '<h1>Wrong Request Function</h1>'
        pass
