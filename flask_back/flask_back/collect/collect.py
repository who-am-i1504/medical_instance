from flask import (request, jsonify, Blueprint)
from flask_back import db, jsonschema, ValidationError, log
from flask_back.dao.sql import CollectResult
import flask_back.constant as cnts
import copy
import datetime

bp = Blueprint('collect', __name__, url_prefix='/collect')

@bp.route('/start', methods=['POST'])
@jsonschema.validate('collect', 'start')
def start():

    # 启动传输规则监测
    back = copy.deepcopy(cnts.back_message)
    json_data = request.get_json()

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))

    collect = CollectResult()
    collect.protocol = json_data['protocol']
    collect.time = json_data['time']
    try:
        db.session.add(collect)
        db.session.flush()
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`collect_result`'))

        back['data'] = {}
        back['data']['id'] = collect.id
        back['data']['protocol'] = collect.protocol
        back['data']['time'] = collect.time
        back['data']['submit'] = collect.submit.strftime('%Y-%m-%d %H:%M:%S')
    except:
        
        log.error(cnts.errorLog(addr, path))

        back['status'] = cnts.database_error
        back['message'] = cnts.database_error_message
        return jsonify(back)
    
    log.info(cnts.successLog(addr, path))

    return jsonify(back)

@bp.route('/result/get_by_page', methods=['POST'])
@jsonschema.validate('collect', 'getByPage')
def getByPage():
    page_size = 10
    back = copy.deepcopy(cnts.back_message)
    json_data = request.get_json()

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))

    if 'size' in json_data.keys():
        page_size = json_data['size']
    try:
        result = db.session.execute('select count(1) from `collect_result`;')
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`collect_result`'))

        back['size'] = result.fetchall()[0][0]
        result = db.session.execute(
            'select `id`, `protocol`, `port`, `time`, `submit` from `collect_result` limit %d,%d;' % ((json_data['page'] - 1)*page_size, page_size))
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`collect_result`'))

        data = result.fetchall()
        back['data'] = []
        for i in data:
            a = {}
            a['id'] = i.id
            a['protocol'] = i.protocol
            a['port'] = i.port
            a['time'] = i.time
            a['submit'] = i.submit.strftime('%Y-%m-%d %H:%M:%S')
            back['data'].append(a)
        # print('here')
    except:
        back['message'] = cnts.database_error_message
        back['status'] = cnts.database_error

        log.error(cnts.errorLog(addr, path))

        return jsonify(back)
    back['page'] = json_data['page']

    log.info(cnts.successLog(addr, path))

    return jsonify(back)

@bp.route('/result/get', methods=['POST'])
@jsonschema.validate('collect', 'getById')
def getOne():
    back = copy.deepcopy(cnts.back_message)
    json_data = request.get_json()

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))

    try:
        result = db.session.execute(
            'select * from `collect_result` where `id` = %d;' % (json_data['id']))
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`collect_result`'))

        data = result.fetchall()
        for i in data:
            a = {}
            a['id'] = i.id
            a['protocol'] = i.protocol
            a['port'] = i.port
            a['time'] = i.time
            a['submit'] = i.submit.strftime('%Y-%m-%d %H:%M:%S')
            if i.start_time is None:
                a['start_time'] = 'null'
            else:
                a['start_time'] = i.start_time.strftime('%Y-%m-%d %H:%M:%S')
            if i.end_time is None:
                a['end_time'] = 'null'
            else:
                a['end_time'] = i.end_time.strftime('%Y-%m-%d %H:%M:%S')
            a['size'] = i.size
            back['data'] = a
    except:
        back['message'] = cnts.database_error_message
        back['status'] = cnts.database_error

        log.error(cnts.errorLog(addr, path))

        return jsonify(back)
    
    log.info(cnts.successLog(addr, path))

    return jsonify(back)

@bp.route('/result/ip_position', methods=['POST'])
@jsonschema.validate('collect', 'ip_position')
def getPosition():
    json_data = request.get_json()
    back = copy.deepcopy(cnts.back_message)

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))

    back['data'] = {
        'ip': json_data['ip'],
        'address': '山东省威海市',
        'equipment': "404医院",
        'institution':"HIT"
    }
    log.info(cnts.successLog(addr, path))
    return jsonify(back)

@bp.errorhandler(ValidationError)
def on_validation_error(e):
    log.warning('%s request %s have a error in its request Json' %
                (request.remote_addr, request.path))
    return jsonify(cnts.params_exception)
