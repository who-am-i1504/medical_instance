import threading
from .pcapParse.Control import MainCollect
from flask import (request, jsonify, Blueprint)
# import db, jsonschema, ValidationError, log, CollectResult
from flask_back import db, jsonschema, ValidationError, log
from flask_back.dao.sql import CollectResult
import flask_back.constant as cnts
import copy
import datetime
# from .company_ip import qcdata

# MainCollect = CollectThread()

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
    json_data['path'] = cnts.PcapPath
    try:
        db.session.add(collect)
        db.session.flush()
        json_data['id'] = collect.id
        if not MainCollect.put(json_data):
            db.session.rollback()
            back['status'] = cnts.collect_error
            back['message'] = cnts.collect_error_message
            back['data'] = {}
            return jsonify(back)
        
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`collect_result`'))

        back['data'] = {}
        back['data']['id'] = collect.id
        if collect.port is None:
            back['data']['port'] = '默认'
        else:
            back['data']['port'] = collect.port
        back['data']['protocol'] = collect.protocol
        back['data']['time'] = str(collect.time) + '分钟'
        back['data']['submit'] = collect.submit.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        
        log.error(cnts.errorLog(addr, path, str(e)))

        back['status'] = cnts.database_error
        back['message'] = str(e)
        return jsonify(back)
    
    log.info(cnts.successLog(addr, path))

    return jsonify(back)

@bp.route('/result/get_by_page', methods=['POST'])
@jsonschema.validate('collect', 'getByPage')
def getByPage():
    page_size = cnts.page_size
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
            'select * from `collect_result` limit %d,%d;' % ((json_data['page'] - 1)*page_size, page_size))
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`collect_result`'))

        data = result.fetchall()
        back['data'] = []
        for i in data:
            a = {}
            a['id'] = i.id
            a['protocol'] = i.protocol
            # print(i)
            if i.port is None:
                a['port'] = '默认'
            else:
                a['port'] = i.port
            a['time'] = str(i.time) + '分钟'
            a['submit'] = i.submit.strftime('%Y-%m-%d %H:%M:%S')
            if i.start_time is None:
                a['start_time'] = '任务执行失败！'
            else:
                a['start_time'] = i.start_time.strftime('%Y-%m-%d %H:%M:%S')
            if i.end_time is None:
                a['end_time'] = '未完'
            else:
                a['end_time'] = i.end_time.strftime('%Y-%m-%d %H:%M:%S')
            if i.size is None:
                a['size'] = "0MB"
            else:
                a['size'] = '%.2f'%(i.size / 1024 / 1024) + 'MB'
            back['data'].append(a)
        # print('here')
    except Exception as e:
        back['message'] = str(e)
        back['status'] = cnts.database_error

        log.error(cnts.errorLog(addr, path, str(e)))

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
            if i.port is None:
                a['port'] = '默认'
            else:
                a['port'] = i.port
            a['time'] = str(i.time) + '分钟'
            a['submit'] = i.submit.strftime('%Y-%m-%d %H:%M:%S')
            if i.start_time is None:
                a['start_time'] = '任务执行失败！'
            else:
                a['start_time'] = i.start_time.strftime('%Y-%m-%d %H:%M:%S')
            if i.end_time is None:
                a['end_time'] = '未完'
            else:
                a['end_time'] = i.end_time.strftime('%Y-%m-%d %H:%M:%S')
            if i.size is None:
                a['size'] = "0MB"
            else:
                a['size'] = '%.2f'%(i.size / 1024 / 1024) + 'MB'
            back['data'] = a
    except Exception as e:
        back['message'] = str(e)
        back['status'] = cnts.database_error

        log.error(cnts.errorLog(addr, path, 'database'))

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
    # l = [json_data['ip']]
    # result = qcdata(l)
    # back['data] = result.pop(0)
    back['data'] = {
        'ip': json_data['ip'],
        'country':'中国',
        'prov':'山东省',
        'city': '威海市',
        'company':"哈尔滨工业大学"
    }
    log.info(cnts.successLog(addr, path))
    return jsonify(back)

@bp.route('/result/ip_position_by_list', methods=['POST'])
@jsonschema.validate('collect', 'ip_position_list')
def getPositionByList():
    json_data = request.get_json()
    back = copy.deepcopy(cnts.back_message)

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))
    # result = qcdata(json_data['ip_list'])
    # back['data] = result
    back['data'] = []
    for i in json_data['ip_list']:
        back['data'].append({
            'ip': i,
            'country':'中国',
            'prov':'山东省',
            'city': '威海市',
            'company':"哈尔滨工业大学"
        })
    log.info(cnts.successLog(addr, path))
    return jsonify(back)

@bp.errorhandler(ValidationError)
def on_validation_error(e):
    log.warning('%s request %s have a error in its request Json' %
                (request.remote_addr, request.path))
    return jsonify(cnts.params_exception)
