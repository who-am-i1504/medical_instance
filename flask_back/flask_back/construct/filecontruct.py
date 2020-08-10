from flask import (request, jsonify, Blueprint, send_from_directory, send_file)
from flask_back import db, jsonschema, ValidationError, log
from flask_back.dao.sql import RuleAstm
import flask_back.constant as cnts
from pypinyin import pinyin, lazy_pinyin
import copy
import redis
import json
from shutil import rmtree
from flask_back.user.user import reids_pool
import os
from . import dpktConstruct as tcp_cons
from . import dpktHttpConstruct as http_cons
from . import PduConstruct as pdu_cons
import time
from concurrent.futures import ThreadPoolExecutor
import threading
import zipfile
from io import BytesIO

threshold = 20
threadPool = ThreadPoolExecutor(max_workers=20)
bp = Blueprint('pcap_contruct', __name__, url_prefix='/construct')

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploadpcap')
ALLOWED_EXTENSIONS = set(['pcap'])
ALLOWED_CONSTRUCT_TYPE = {
    'TCP_CONSTRUCT':tcp_cons.construct,
    'HTTP_DOWNLOAD_CONSTRUCT':http_cons.construct,
    'PDU_CONSTRUCT' : pdu_cons.construct
}
ALLOWED_CONSTRUCT_DIRS = {
    'TCP_CONSTRUCT':'TCP',
    'HTTP_DOWNLOAD_CONSTRUCT':'HTTP',
    'PDU_CONSTRUCT' : 'PDU'
}


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@bp.route('/upload', methods=['GET', 'POST'])
def upload():
    back = copy.deepcopy(cnts.back_message)
    sessionid = request.headers['X-Token']
    try:
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = ''.join(lazy_pinyin(file.filename))
            if not os.path.exists(os.path.join(UPLOAD_FOLDER, sessionid)):
                os.mkdir(os.path.join(UPLOAD_FOLDER, sessionid))
            file.save(os.path.join(UPLOAD_FOLDER, sessionid, filename))
            back['data'] = filename
        else:
            back['status'] = 506
            back['message'] = '文件格式不支持'
    except Exception as e:
        back['status'] = 505
        back['message'] = str(e)
        return jsonify(back)
    return jsonify(back)

@bp.route('/delete', methods=['POST'])
@jsonschema.validate('construct', 'deleteFile')
def delete():
    back = copy.deepcopy(cnts.back_message)
    sessionid = request.headers['X-Token']
    json_data = request.get_json()
    try:
        os.remove(os.path.join(UPLOAD_FOLDER, sessionid, json_data['filename']))
    except Exception as e:
        back['status'] = 500
        back['message'] = str(e)
        return jsonify(back)
    return jsonify(back)


@bp.route('/deleteBySessionId', methods=['POST'])
def deleteall():
    back = copy.deepcopy(cnts.back_message)
    sessionid = request.headers['X-Token']
    try:
        rmtree(os.path.join(UPLOAD_FOLDER, sessionid), ignore_errors=False, onerror=None)
    except Exception as e:
        back['status'] = 500
        back['message'] = str(e)
        return jsonify(back)
    return jsonify(back)

@bp.route('/getType', methods=['GET','POST'])
def getType():
    back = copy.deepcopy(cnts.back_message)
    back['data'] = ALLOWED_CONSTRUCT_TYPE
    return jsonify(back)

@bp.route('/construct_params', methods=['POST'])
@jsonschema.validate('construct', 'consParam')
def cons_params():
    back = copy.deepcopy(cnts.back_message)
    jsno_data = request.get_json()
    sessionid = request.headers['X-Token']
    try:
        if os.path.exists(os.path.join(UPLOAD_FOLDER, sessionid, ALLOWED_CONSTRUCT_DIRS[jsno_data['cons_type']])):
            rmtree(os.path.join(UPLOAD_FOLDER, sessionid, ALLOWED_CONSTRUCT_DIRS[jsno_data['cons_type']]), ignore_errors=False, onerror=None)
        t = threadPool.submit(ALLOWED_CONSTRUCT_TYPE[jsno_data['cons_type']], os.path.join(UPLOAD_FOLDER, sessionid), jsno_data['filename'], ALLOWED_CONSTRUCT_DIRS[jsno_data['cons_type']])
        time.sleep(10)
        path = t.result()
        back['data'] = {
            'name':ALLOWED_CONSTRUCT_DIRS[jsno_data['cons_type']],
            'type':'dir',
            'children':[]
        }
        for i in os.listdir(path):
            back['data']['children'].append({
                'name':i,
                'type':'file'
            })
    except Exception as e:
        back['status'] = 406
        back['message'] = str(e)
        return jsonify(back)
    return jsonify(back)


@bp.route('/downfile', methods=['POST'])
@jsonschema.validate('construct', 'file_para')
def downloadFile():
    back = copy.deepcopy(cnts.back_message)
    json_data = request.get_json()
    sessionid = request.headers['X-Token']
    try:
        return send_from_directory(os.path.join(UPLOAD_FOLDER, sessionid), json_data['filename'], as_attachment=True)
    except Exception as e:
        back['status'] = 509
        back['message'] = str(e)
        return jsonify(back)
    return jsonify(back)

@bp.route('/downDirectory', methods=['POST'])
@jsonschema.validate('construct', 'dir_para')
def downloadDirectory():
    back = copy.deepcopy(cnts.back_message)
    json_data = request.get_json()
    sessionid = request.headers['X-Token']
    memory_file = BytesIO()
    try:
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            path = os.path.join(UPLOAD_FOLDER, sessionid, json_data['dirname'])
            for i in os.listdir(path):
                with open(os.path.join(path, i), 'rb') as fp:
                    zf.writestr(i, fp.read())
        memory_file.seek(0)
        return send_file(memory_file, attachment_filename='download.zip', as_attachment=True)
    except Exception as e:
        back['status'] = 509
        back['message'] = str(e)
        return jsonify(back)
    return jsonify(back)


@bp.errorhandler(ValidationError)
def astm_error(e):
    log.warning('%s request %s have a error in its request Json  %s' %
                (request.remote_addr, request.path, request.get_json()))
    return jsonify(cnts.params_exception)
