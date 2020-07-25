from flask import (request, jsonify, Blueprint, redirect)
from flask_back import db, jsonschema, ValidationError,log
from flask_back.dao.sql import RuleHl7
import flask_back.constant as cnts
import xlrd
import time
import os
import copy
import redis
from flask_back.user.user import reids_pool
# import sqlalchemy.exc.OperationalError as OperationError

bp = Blueprint('rule_hl7', __name__, url_prefix='/rule/hl7')

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

@bp.route('/add_by_excel', methods=['POST'])
def hl7_rule_add_by_excel():
    status = cnts.status
    message = cnts.message
    file = request.files['file']
    # print(file)
    filename = ('./' + str(round(time.time()*1000000)) + request.remote_addr + file.filename)
    file.save(filename)
    error_num = 0
    correct_num = 0
    wb = xlrd.open_workbook(filename)
    try:
        ws = wb.sheets()[0]
        for i in range(ws.nrows):
            inSql = RuleHl7()
            # inSql.id = 10
            inSql.value = ws.cell_value(i, 0)
            print(type(inSql.value))
            if not isinstance(inSql.value, str):
                error_num = error_num + 1
                status = 201
                continue
            try:
                db.session.add(inSql)
                correct_num = correct_num + 1
            except:
                error_num = error_num + 1
                status = 201
        try:
            db.session.commit()
        except:
            status = cnts.database_error
            message = cnts.database_error_message
        del ws
    except:
        status = cnts.file_error
        message = cnts.file_error_message
    del wb
    if status == 201:
        message = cnts.excel_add_error_message(error_num, correct_num)
    json_back = {}
    json_back['status'] = status
    json_back['message'] = message
    os.remove(filename)
    return jsonify(json_back)

@bp.route('/add', methods=['POST'])
@jsonschema.validate('hl7', 'add')
def hl7_rule_add():
    back = copy.deepcopy(cnts.back_message)
    data = None
    json_data = request.get_json()
    for character in cnts.special_character.keys():
        if character in json_data['value']:
            json_data['value'] = json_data['value'].replace(character, cnts.special_character[character])
    # json_data['value'] = json_data['value'].replace('\\r', '\r')
    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))

    inSql = RuleHl7()
    # inSql.id = 10
    inSql.value = json_data['value']
    try:
        db.session.add(inSql)
        db.session.flush()
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`rule_hl7`'))

        data = inSql
    except:
        back['status'] = cnts.database_error
        back['message'] = cnts.database_error_message

        log.error(cnts.errorLog(addr, path))

        return jsonify(back)
    back['data'] = {}
    back['data']['id'] = data.id
    back['data']['value'] = data.value
    log.info(cnts.successLog(addr, path))
    return jsonify(back)

@bp.route('/update', methods=['POST'])
@jsonschema.validate('hl7', 'update')
def hl7_rule_update():
    back = copy.deepcopy(cnts.back_message)
    json_data = request.get_json()
    for character in cnts.special_character.keys():
        if character in json_data['value']:
            json_data['value'] = json_data['value'].replace(character, cnts.special_character[character])
    # json_data['value'] = json_data['value'].replace('\\r', '\r')

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))

    hl7_update = RuleHl7()
    hl7_update.id = json_data['id']
    hl7_update.value = json_data['value']
    try:
        current = RuleHl7.query.filter(RuleHl7.id == hl7_update.id).first()
        current.value = hl7_update.value
        db.session.commit()
        
        log.info(cnts.databaseSuccess(addr, path, '`rule_hl7`'))

    except:
        back['message'] = cnts.database_error_message
        back['status'] = cnts.database_error

        log.error(cnts.errorLog(addr, path))

        return jsonify(back)
    
    log.info(cnts.successLog(addr, path))

    return jsonify(back)

@bp.route('/delete', methods=['POST'])
@jsonschema.validate('hl7', 'delete')
def hl7_rule_delete():
    back = copy.deepcopy(cnts.back_message)
    json_data = request.get_json()

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))

    if 'value' in json_data.keys():
        try:
            current = RuleHl7.query.filter(RuleHl7.id == json_data['id']).first()
            db.session.commit()
            log.info(cnts.databaseSuccess(addr, path, '`rule_hl7`'))
            if current.ip != json_data['value']:
                back['status'] = cnts.monitor_delete
                back['message'] = cnts.monitor_delete_message


                log.info(cnts.successLog(addr, path))

                return jsonify(back)
        except:

            back['status'] = cnts.database_error
            back['message'] = cnts.database_error_message

            log.error(cnts.errorLog(addr, path))

            return jsonify(back)
    try:
        db.session.execute('delete from `rule_hl7` where `id` = %d;' % (json_data['id']))
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`rule_hl7`'))

    except:
        back['status'] = cnts.database_error
        back['message'] = cnts.database_error_message

        log.error(cnts.errorLog(addr, path))

        return jsonify(back)
    
    log.info(cnts.successLog(addr, path))

    return jsonify(back)


@bp.route('/get', methods=['POST'])
@jsonschema.validate('hl7', 'get')
def hl7_rule_get():
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
        result = db.session.execute('select count(1) from `rule_hl7`;')
        db.session.commit()
        log.info(cnts.databaseSuccess(addr, path, '`rule_hl7`'))
        size = result.fetchall()[0][0]
        result = db.session.execute('select * from `rule_hl7` limit %d,%d;'%((json_data['page'] - 1)*page_size, page_size))
        db.session.commit()
        log.info(cnts.databaseSuccess(addr, path, '`rule_hl7`'))
        data = result.fetchall()
        back['data'] = []
        for i in data:
            a = {}
            a['id'] = i.id
            a['value'] = i.value
            back['data'].append(a)
    except:
        back['message'] = cnts.database_error_message
        back['status'] = cnts.database_error

        log.error(cnts.errorLog(addr, path))

        return jsonify(back)
    back['page'] = json_data['page']
    back['size'] = size

    log.info(cnts.successLog(addr, path))

    return jsonify(back)


@bp.route('/getOne', methods=['POST'])
@jsonschema.validate('hl7', 'getOne')
def getOne():
    json_data = request.get_json()
    back = copy.deepcopy(cnts.back_message)
    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))
    try:
        result = db.session.execute('select * from `rule_hl7` where `id` = %d;' % (json_data['id']))
        db.session.commit()
        log.info(cnts.databaseSuccess(addr, path, '`rule_hl7`'))
        data = result.fetchall()[0]
        back['data'] = {}
        back['data']['id'] = data.id
        back['data']['value'] = data.value
    except:
        message = cnts.database_error
        back['status'] = cnts.database_error
        back['message'] = cnts.database_error_message
        log.error(cnts.errorLog(addr, path))
        return jsonify(back)
    log.info(cnts.successLog(addr, path))
    return jsonify(back)



@bp.errorhandler(ValidationError)
def on_validation_error(e):
    log.warning('%s request %s have a error in its request Json  %s' %
                (request.remote_addr, request.path, request.get_json()))
    return jsonify(cnts.params_exception)
