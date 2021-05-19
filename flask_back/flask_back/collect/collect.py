import threading
from .pcapParse.Control import MainCollect
from flask import (request, jsonify, Blueprint)
# import db, jsonschema, ValidationError, log, CollectResult
from flask_back import db, jsonschema, ValidationError, log
from flask_back.dao.sql import CollectResult
from flask_back.constant import Ip2Geo
import flask_back.constant as cnts
import copy
import datetime
import redis
import json
from flask_back.user.user import reids_pool
# from .company_ip import qcdata

# MainCollect = CollectThread()

bp = Blueprint('collect', __name__, url_prefix='/collect')

@bp.after_request
def record_log(response):
    
    try:
        session=redis.Redis(connection_pool=reids_pool)
        if 'X-Token' in request.headers.keys():
            sessionid = request.headers['X-Token']
            if session.exists(sessionid):
                # print('1')
                req = json.dumps(request.get_json())
                # print('2')
                resp = ''
                if 'get' in request.path:
                    resp = '......'
                else:
                    resp = json.dumps(response.get_json())
                    if len(resp) > 100:
                        resp = '......'
                # print('3')
                authority = session.hget(sessionid, 'authority')
                # print('4')
                name = session.hget(sessionid, 'username')
                # print('5')
                uuid = session.hget(sessionid, 'uuid')
                # print('6')
                db.session.execute("INSERT INTO `logs` VALUES(NULL, '%s', '%s', '%s', '%s', NOW(), '%s', '%s', %s);" % (str(request.remote_addr), str(request.path), req, resp, str(uuid), str(name), str(authority)))
                db.session.commit()
    except Exception as e:
        
        pass
    finally:
        return response

@bp.before_request
def validSession():
    back = {
        "status":cnts.quit_login,
        "message":cnts.quit_login_message,
        "data":{}
    }
    if request.path == '/login' or request.path == '/salt':
        return None
    session=redis.Redis(connection_pool=reids_pool)
    if 'X-Token' in request.headers.keys():
        sessionid = request.headers['X-Token']
        if session.exists(sessionid):
            if 'update' in request.path or 'add' in request.path or 'delete' in request.path:
                if cnts.validEditor(session.hget(sessionid, 'authority')):
                    return None
                else:
                    back['message'] = '您的权限不足'
                    return jsonify(back)
            elif 'start' in request.path:
                if cnts.validCollect(session.hget(sessionid, 'authority')):
                    return None
                else:
                    back['message'] = '您的权限不足'
                    return jsonify(back)
            return None
    return jsonify(back)

@bp.route('/get', methods=['POST'])
def getSize():
    back = copy.deepcopy(cnts.back_message)

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, ' '))

    try:

        result = db.session.execute(
            'SELECT date(`submit`) as `date`, SUM(`size`) as `size`\
            FROM `collect_result`\
            GROUP BY `date`;')
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`collect_result`'))

        data = result.fetchall()
        back['data'] = []
        for i in data:
            a = {}
            a['date'] = i['date'].strftime('%Y-%m-%d')
            a['数据量'] = i['size']
            back['data'].append(a)
        # print('here')
    except:
        back['message'] = cnts.database_error_message
        back['status'] = cnts.database_error

        log.error(cnts.errorLog(addr, path, 'database'))

        return jsonify(back)

    log.info(cnts.successLog(addr, path))

    return jsonify(back)

@bp.route('/state', methods=['GET'])
def state():
    back = copy.deepcopy(cnts.back_message)
    back['data'] = MainCollect.getState() - 1
    return jsonify(back)

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
    except:
        
        log.error(cnts.errorLog(addr, path, 'database'))

        back['status'] = cnts.database_error
        back['message'] = cnts.database_error_message
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

    if 'pageSize' in json_data.keys():
        page_size = json_data['pageSize']
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
    except:
        back['message'] = cnts.database_error_message
        back['status'] = cnts.database_error

        log.error(cnts.errorLog(addr, path, 'database'))

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
    except:
        back['message'] = cnts.database_error_message
        back['status'] = cnts.database_error

        log.error(cnts.errorLog(addr, path, 'database'))

        return jsonify(back)
    
    log.info(cnts.successLog(addr, path))

    return jsonify(back)


@bp.route('/result/delete', methods=['POST'])
@jsonschema.validate('collect', 'getById')
def deleteOne():
    back = copy.deepcopy(cnts.back_message)
    json_data = request.get_json()

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))

    try:
        result = db.session.execute(
            'delete from `collect_result` where `id` = %d;' % (json_data['id']))
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`collect_result`'))
    except:
        back['message'] = cnts.database_error_message
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
    res = Ip2Geo(json_data['ip'])
    back['data'] = {
        'ip': json_data['ip'],
        'country':res['country'],
        'prov':res['province'],
        'city': res['city'],
        'company':"无",
        'lngwgs':res['lngwgs'],
        'latwgs':res['latwgs']
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
        res = Ip2Geo(json_data['ip'])
        back['data'].append({
            'ip': json_data['ip'],
            'country':res['country'],
            'prov':res['province'],
            'city': res['city'],
            'company':"无",
            'lngwgs':res['lngwgs'],
        '   latwgs':res['latwgs']
        })
    log.info(cnts.successLog(addr, path))
    return jsonify(back)

@bp.errorhandler(ValidationError)
def on_validation_error(e):
    log.warning('%s request %s have a error in its request Json' %
                (request.remote_addr, request.path))
    return jsonify(cnts.params_exception)
