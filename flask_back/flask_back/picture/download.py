from flask import (request, jsonify, Blueprint, render_template,send_file, make_response, send_from_directory, abort)
from flask_back import db, jsonschema, ValidationError, log
import os
import flask_back.constant as cnts
from flask_back.constant import PicturePath
import redis
from flask_back.user.user import reids_pool
import copy
import zipfile
from io import BytesIO
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

@bp.route('/log/download', methods=['GET'])
def logDownload():
    return send_from_directory(os.path.join(os.getcwd()), 'current.log', as_attachment=True)

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

@bp.route('/downDirectory', methods=['GET','POST'])
@jsonschema.validate('picture', 'dictory')
def downloadDirectory():
    back = copy.deepcopy(cnts.back_message)
    json_data = request.get_json()
    memory_file = BytesIO()
    try:
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            path = os.path.join(os.getcwd(), PicturePath)
            for i in json_data['pictures']:
                # if not os.path.exists(os.path.join(path, i)):
                # print(os.path.join(path, i))
                # zf.write(os.path.join(path, i), i)
                    # continue
                # try:
                with open(os.path.join(path, i), 'rb') as fp:
                    zf.writestr(i, fp.read())
            # zf.close()
                # except :
                #     continue
        memory_file.seek(0)
        return send_file(memory_file, attachment_filename='download.zip', as_attachment=True)
    except Exception as e:
        back['status'] = 509
        back['message'] = str(e)
        return jsonify(back)
    return jsonify(back)

@bp.route('/test', methods=['GET'])
def test():
    return send_from_directory(r'/home/white/Documents/project/medical_instance', 'name.zip', as_attachment=True)

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
