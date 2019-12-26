from flask import (request, jsonify, Blueprint)
from flask_back import db
from flask_back.dao.sql import RuleDicom
import flask_back.constant as cnts

bp = Blueprint('rule_dicom', __name__, url_prefix='/rule/dicom')

@bp.route('/add', methods=['POST'])
def dicom_rule_add():
    data = None
    status = cnts.status
    message = cnts.message
    back_data = {}

    json_data = request.get_json()
    inSql = RuleDicom()
    # inSql.id = 10
    inSql.value = json_data['value']
    if isinstance(inSql.value, int):
        try:
            db.session.add(inSql)
            db.session.commit()
            db.session.flush()
            data = inSql
        except:
            status = cnts.database_error
            message = cnts.database_error
    else:
        status = cnts.type_error
        message = cnts.type_error_message
    back_data['status'] = status
    back_data['message'] = message
    back_data['data'] = {}
    if data != None:
        back_data['data']['id'] = data.id
        back_data['data']['value'] = data.value
    return jsonify(back_data)

@bp.route('/update', methods=['POST'])
def dicom_rule_update():
    status = cnts.status
    message = cnts.message
    json_data = request.get_json()
    dicom_update = RuleDicom()
    dicom_update.id = json_data['id']
    dicom_update.value = json_data['value']
    if isinstance(dicom_update.id, int) and isinstance(dicom_update.value, int):
        try:
            current = RuleDicom.query.filter(RuleDicom.id == dicom_update.id).first()
            current.value = dicom_update.value
            db.session.commit()
        except:
            message = cnts.database_error
            status = cnts.database_error
    else:
        message = cnts.type_error_message
        status = cnts.type_error
    back_data = {}
    back_data['status'] = status
    back_data['message'] = message
    return jsonify(back_data)

@bp.route('/get', methods=['POST'])
def dicom_rule_get():
    page_size = 20
    pageNo = 1
    size = 0
    status = cnts.status
    message = cnts.message
    data = None
    json_data = request.get_json()
    if isinstance(json_data['page'], int):
        pageNo = json_data['page']
    try:
        result = db.session.execute('select count(1) from `rule_dicom`;')
        db.session.commit()
        size = result.fetchall()[0][0]
        result = db.session.execute('select * from `rule_dicom` limit %d,%d;'%((pageNo - 1)*page_size, page_size))
        db.session.commit()
        data = result.fetchall()
    except:
        message = cnts.database_error_message
        status = cnts.database_error
    back_data = {}
    back_data['status'] = status
    back_data['message'] = message
    back_data['data'] = []
    for i in data:
        a = {}
        a['id'] = i.id
        a['value'] = i.value
        back_data['data'].append(a)
    back_data['page'] = pageNo
    back_data['size'] = size
    return jsonify(back_data)

@bp.route('/delete', methods=['POST'])
def dicom_rule_delete():
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
                current = RuleDicom.query.filter(RuleDicom.id == json_data['id']).first()
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
