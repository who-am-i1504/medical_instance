from flask import (request, jsonify, Blueprint)
from flask_back import db, jsonschema, ValidationError, log
from flask_back.dao.sql import RuleDicom
import flask_back.constant as cnts
import copy
import redis
from flask_back.user.user import reids_pool
import json

bp = Blueprint('rule_dicom', __name__, url_prefix='/rule/dicom')

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
            return None
    return jsonify(back)

@bp.route('/add_Integer', methods=['POST'])
@jsonschema.validate('dicom', 'add')
def dicom_rule_add():
    back = copy.deepcopy(cnts.back_message)
    json_data = request.get_json()

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))

    inSql = RuleDicom()
    # inSql.id = 10
    inSql.value = json_data['value']
    try:
        db.session.add(inSql)
        db.session.flush()
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`rule_dicom`'))

        back['data'] = {}
        back_data['data']['id'] = inSql.id
        back_data['data']['value'] = inSql.value
    except:

        log.error(cnts.errorLog(addr, path))

        back['status'] = cnts.database_error
        back['message'] = cnts.database_error
        return jsonify(back)

    log.info(cnts.successLog(addr, path))

    return jsonify(back)


@bp.route('/add', methods=['POST'])
@jsonschema.validate('dicom', 'add_string')
def rule_add_string():
    data = None
    back = copy.deepcopy(cnts.back_message)
    json_data = request.get_json()
    for character in cnts.special_character.keys():
        if character in json_data['value']:
            json_data['value'] = json_data['value'].replace(character, cnts.special_character[character])
    # json_data['value'] = json_data['value'].replace('\\r', '\r')

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))

    inSql = RuleDicom()
    # inSql.id = 10
    inSql.value = int(json_data['value'])
    try:
        db.session.add(inSql)
        db.session.flush()
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`rule_dicom`'))

        data = inSql
        back['data'] = {}
        back['data']['id'] = data.id
        back['data']['value'] = data.value
    except:

        log.error(cnts.errorLog(addr, path))

        back['status'] = cnts.database_error
        back['message'] = cnts.database_error
        return jsonify(back)

    log.info(cnts.successLog(addr, path))

    return jsonify(back)


@bp.route('/update', methods=['POST'])
@jsonschema.validate('dicom', 'update')
def dicom_rule_update():
    back = copy.deepcopy(cnts.back_message)
    json_data = request.get_json()
    json_data['value'] = json_data['value'].replace('\\r', '\r')

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))

    dicom_update = RuleDicom()
    dicom_update.id = json_data['id']
    dicom_update.value = json_data['value']
    try:
        current = RuleDicom.query.filter(
            RuleDicom.id == dicom_update.id).first()
        current.value = dicom_update.value
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`rule_dicom`'))

    except:

        log.error(cnts.errorLog(addr, path))

        back['message'] = cnts.database_error
        back['status'] = cnts.database_error
        return jsonify(back)
    
    log.info(cnts.successLog(addr, path))

    return jsonify(back)


@bp.route('/get', methods=['POST'])
@jsonschema.validate('dicom', 'get')
def dicom_rule_get():
    page_size = cnts.page_size
    size = 0
    back = copy.deepcopy(cnts.back_message)
    data = None
    json_data = request.get_json()

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))
    if 'pageSize' in json_data.keys():
        page_size = json_data['pageSize']
    try:
        result = db.session.execute('select count(1) from `rule_dicom`;')
        db.session.commit()


        log.info(cnts.databaseSuccess(addr, path, '`rule_dicom`'))

        size = result.fetchall()[0][0]
        result = db.session.execute(
            'select * from `rule_dicom` limit %d,%d;' % ((json_data['page'] - 1)*page_size, page_size))
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`rule_dicom`'))

        data = result.fetchall()
        back['data'] = []
        for i in data:
            a = {}
            a['id'] = i.id
            a['value'] = i.value
            back['data'].append(a)
    except:

        log.error(cnts.errorLog(addr, path))

        back['message'] = cnts.database_error_message
        back['status'] = cnts.database_error
        return jsonify(back)
    back['page'] = json_data['page']
    back['size'] = size

    log.info(cnts.successLog(addr, path))

    return jsonify(back)


@bp.route('/delete', methods=['POST'])
@jsonschema.validate('dicom', 'delete')
def dicom_rule_delete():
    back = copy.deepcopy(cnts.back_message)
    json_data = request.get_json()

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))

    if 'value' in json_data.keys():
        try:
            current = RuleDicom.query.filter(
                RuleDicom.id == json_data['id']).first()
            db.session.commit()

            log.info(cnts.databaseSuccess(addr, path, '`rule_dicom`'))

            if current.ip != json_data['value']:
                back['status'] = cnts.monitor_delete
                back['message'] = cnts.monitor_delete_message
                
                log.info(cnts.successLog(addr, path))

                return jsonify(back)
        except:

            log.error(cnts.errorLog(addr, path))

            back['status'] = cnts.database_error
            back['message'] = cnts.database_error_message
            return jsonify(back)
    try:
        db.session.execute(
            'delete from `rule_dicom` where `id` = %d;' % (json_data['id']))
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`rule_dicom`'))

        pass
    except:

        log.error(cnts.errorLog(addr, path))

        back['status'] = cnts.database_error
        back['message'] = cnts.database_error_message
        return jsonify(back)
    
    log.info(cnts.successLog(addr, path))

    return jsonify(back)


@bp.route('/getOne', methods=['POST'])
@jsonschema.validate('dicom', 'getOne')
def get_one():
    back = copy.deepcopy(cnts.back_message)
    json_data = request.get_json()

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))

    try:
        result = db.session.execute(
            'select * from `rule_dicom` where `id` = %d;' % (json_data['id']))
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`rule_dicom`'))

        data = result.fetchall()[0]
        back['data'] = {}
        back['data']['id'] = data.id
        back['data']['value'] = data.value
    except:

        log.error(cnts.errorLog(addr, path))

        back['status'] = cnts.database_error
        back['message'] = cnts.database_error_message
        return jsonify(back)
    
    log.info(cnts.successLog(addr, path))

    return jsonify(back)


@bp.errorhandler(ValidationError)
def dicom_error(e):
    log.warning('%s request %s have a error in its request Json  %s' %
                (request.remote_addr, request.path, request.get_json()))
    return jsonify(cnts.params_exception)
