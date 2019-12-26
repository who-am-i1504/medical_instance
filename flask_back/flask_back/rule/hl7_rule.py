from flask import (request, jsonify, Blueprint)
from flask_back import db
from flask_back.dao.sql import RuleHl7
import flask_back.constant as cnts
import xlrd
import time
import os

bp = Blueprint('rule_hl7', __name__, url_prefix='/rule/hl7')

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
def hl7_rule_add():
    data = None
    status = cnts.status
    message = cnts.message
    back_data = {}

    json_data = request.get_json()
    inSql = RuleHl7()
    # inSql.id = 10
    inSql.value = json_data['value']
    try:
        db.session.add(inSql)
        db.session.commit()
        db.session.flush()
        data = inSql
    except:
        status = cnts.database_error
        message = cnts.database_error_message
    back_data['status'] = status
    back_data['message'] = message
    back_data['data'] = {}
    if data != None:
        back_data['data']['id'] = data.id
        back_data['data']['value'] = data.value
    return jsonify(back_data)

@bp.route('/update', methods=['POST'])
def hl7_rule_update():
    status = cnts.status
    message = cnts.message
    json_data = request.get_json()
    hl7_update = RuleHl7()
    hl7_update.id = json_data['id']
    hl7_update.value = json_data['value']
    if isinstance(hl7_update.id, int):
        try:
            current = RuleHl7.query.filter(RuleHl7.id == hl7_update.id).first()
            current.value = hl7_update.value
            db.session.commit()
        except:
            message = cnts.database_error_message
            status = cnts.database_error
    else:
        message = cnts.type_error_message
        status = cnts.type_error
    back_data = {}
    back_data['status'] = status
    back_data['message'] = message
    return jsonify(back_data)

@bp.route('/delete', methods=['POST'])
def hl7_rule_delete():
    status = cnts.status
    message = cnts.message
    json_data = request.get_json()
    back_data = {}
    if 'id' not in json_data.keys():
        back_data['status'] = cnts.params_error
        back_data['message'] = cnts.params_error_message
        return jsonify(back_data)
    if isinstance(json_data['id'], int):
        if 'value' in json_data.keys() and isinstance(json_data['value'], str):
            try:
                current = RuleHl7.query.filter(RuleHl7.id == json_data['id']).first()
                db.session.commit()
                if current.ip != json_data['value']:
                    back_data['status'] = cnts.monitor_delete
                    back_data['message'] = cnts.monitor_delete_message
                    return jsonify(back_data)
            except:
                back_data['status'] = cnts.database_error
                back_data['message'] = cnts.database_error_message
                return jsonify(back_data)
        try:
            db.session.execute('delete from `rule_hl7` where `id` = %d;' % (json_data['id']))
            db.session.commit()
            pass
        except:
            status = cnts.database_error
            message = cnts.database_error_message
    else:
        status = cnts.type_error
        message = cnts.type_error_message
    back_data['status'] = status
    back_data['message'] = message
    return jsonify(back_data)


@bp.route('/get', methods=['POST'])
def hl7_rule_get():
    page_size = 20
    pageNo = 1
    size = 0
    status = cnts.status
    message = cnts.message
    data = None
    json_data = request.get_json()
    if 'page' not in json_data.keys():
        return None
    if isinstance(json_data['page'], int):
        pageNo = json_data['page']
        try:
            result = db.session.execute('select count(1) from `rule_hl7`;')
            db.session.commit()
            size = result.fetchall()[0][0]
            result = db.session.execute('select * from `rule_hl7` limit %d,%d;'%((pageNo - 1)*page_size, page_size))
            db.session.commit()
            data = result.fetchall()
        except:
            message=cnts.database_error_message
            status = cnts.database_error
    else:
        message = cnts.type_error_message
        status = cnts.type_error
    back_data = {}
    back_data['status'] = status
    back_data['message'] = message
    back_data['data'] = []
    for i in data:
        a = {}
        a['id'] = i.id
        a['value'] = i.id
        back_data['data'].append(a)
    back_data['page'] = pageNo
    back_data['size'] = size
    return jsonify(back_data)

