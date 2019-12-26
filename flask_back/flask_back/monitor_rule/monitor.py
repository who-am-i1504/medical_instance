from flask import (request, jsonify, Blueprint)
from flask_back import db
import flask_back.constant as cnts
from flask_back.dao.sql import MonitorRule, MessageMain, AAssociateRQ, AAssociateAC, AAssociateRJ, AReleaseRQ, \
    AReleaseRP, ABort, PDataTF

bp = Blueprint('monitor', __name__, url_prefix='/monitor/rule')


@bp.route('/get', methods=['POST'])
def monitor_get():
    status = cnts.status
    message = cnts.message
    page_size = cnts.page_size
    pageNo = 1
    size = 0
    data = None
    json_data = request.get_json()
    if 'page' not in json_data.keys():
        return None
    if isinstance(json_data['page'], int):
        pageNo = json_data['page']
        try:
            result = db.session.execute('select count(1) from `monitor_rule`;')
            db.session.commit()
            size = result.fetchall()[0][0]
            result = db.session.execute(
                'select * from `monitor_rule` limit %d,%d;' % ((pageNo - 1) * page_size, page_size))
            db.session.commit()
            data = result.fetchall()
        except:
            message = cnts.database_error_message
            status = cnts.database_error
    else:
        status = cnts.type_error
        message = cnts.type_error_message

    back_data = {}
    back_data['status'] = status
    back_data['message'] = message
    back_data['data'] = []
    if not data == None:
        for i in data:
            a = {}
            a['id'] = i.id
            a['ip'] = i.ip
            back_data['data'].append(a)
    back_data['page'] = pageNo
    back_data['size'] = size
    return jsonify(back_data)


@bp.route('/add', methods=['POST'])
def monitor_add():
    status = cnts.status
    message = cnts.message
    data = None
    json_data = request.get_json()
    if 'ip' not in json_data.keys():
        return None
    if isinstance(json_data['ip'], str):
        insert_item = MonitorRule()
        insert_item.ip = json_data['ip']
        try:
            db.session.add(insert_item)
            # db.session.flush()
            db.session.commit()
            data = insert_item
        except:
            message = cnts.database_error_message
            status = cnts.database_error
    else:
        status = cnts.type_error
        message = cnts.type_error_message

    back_data = {}
    back_data['status'] = status
    back_data['message'] = message
    if not data == None:
        a = {}
        a['id'] = data.id
        a['ip'] = data.ip
        back_data['data'] = a
    return jsonify(back_data)


@bp.route('/update', methods=['POST'])
def monitor_update():
    status = cnts.status
    message = cnts.message
    request_params = ['id', 'ip']
    json_data = request.get_json()
    back_data = {}
    param_num = 0
    for param in json_data.keys():
        if param in request_params:
            param_num += 1
            pass
    if param_num < 2:
        back_data['status'] = cnts.params_error
        back_data['message'] = cnts.params_error_message
        return jsonify(back_data)
    update = MonitorRule()
    if isinstance(json_data['id'], int) and isinstance(json_data['ip'], str):
        update.id = json_data['id']
        update.ip = json_data['ip']
        try:
            current = MonitorRule.query.filter(MonitorRule.id == update.id).first()
            current.ip = update.ip
            db.session.commit()
        except:
            status = cnts.database_error
            message = cnts.database_error_message
    else:
        status = cnts.type_error
        message = cnts.type_error_message
    back_data['status'] = status
    back_data['message'] = message
    return jsonify(back_data)


@bp.route('/delete', methods=['POST'])
def monitor_delete():
    status = cnts.status
    message = cnts.message
    json_data = request.get_json()
    back_data = {}
    if 'id' not in json_data.keys():
        back_data['status'] = cnts.params_error
        back_data['message'] = cnts.params_error_message
        return jsonify(back_data)
    if isinstance(json_data['id'], int):
        if 'ip' in json_data.keys() and isinstance(json_data['ip'], str):
            try:
                current = MonitorRule.query.filter(MonitorRule.id == json_data['id']).first()
                db.session.commit()
                if current.ip != json_data['ip']:
                    back_data['status'] = cnts.monitor_delete
                    back_data['message'] = cnts.monitor_delete_message
                    return jsonify(back_data)
            except:
                back_data['status'] = cnts.database_error
                back_data['message'] = cnts.database_error_message
                return jsonify(back_data)
        try:
            db.session.execute('delete from `monitor_rule` where `id` = %d;' % (json_data['id']))
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


@bp.route('/result', methods=['POST'])
def monitor_result():
    status = cnts.status
    message = cnts.message
    json_data = request.get_json()
    back_data = {}
    if 'ip' not in json_data.keys():
        back_data['status'] = cnts.params_error
        back_data['status'] = cnts.params_error_message
        return jsonify(back_data)
    if isinstance(json_data['ip'], str):
        try:
            current = MonitorRule.query.filter(MonitorRule.ip == json_data['ip']).first()
            if current is None or 'id' not in current.keys() or current['id'] is None or current['id'] <= 0:
                back_data['status'] = cnts.ip_not_found
                back_data['message'] = cnts.ip_not_found_message
                return jsonify(back_data)
        except:
            status = cnts.database_error
            message = cnts.database_error_message
        try:
            hl7_result = db.session.execute('select COUNT(1), SUM(size) from `message` '
                                            'where %s = `send_ip_port` or %s = `receive_ip_port`' % (
                                                json_data['ip'] + ':%', json_data['ip'] + ':%')).first()
            dicom1_result = db.session.execute('select COUNT(1), SUM(pdu_length) from `a_associate_rq` '
                                               'where %s = `send_ip_port` or %s = `receive_ip_port`'
                                               % (json_data['ip'] + ':%', json_data['ip'] + ':%')).first()
            dicom2_result = db.session.execute('select COUNT(1), SUM(pdu_length) from `a_associate_ac` '
                                               'where %s = `send_ip_port` or %s = `receive_ip_port`' % (
                                                   json_data['ip'] + ':%', json_data['ip'] + ':%')).first()
            dicom3_result = db.session.execute('select COUNT(1), SUM(pdu_length) from `a_associate_rj` '
                                               'where %s = `send_ip_port` or %s = `receive_ip_port`' % (
                                                   json_data['ip'] + ':%', json_data['ip'] + ':%')).first()
            dicom4_result = db.session.execute('select COUNT(1), SUM(pdu_length) from `a_release_rq` '
                                               'where %s = `send_ip_port` or %s = `receive_ip_port`' % (
                                                   json_data['ip'] + ':%', json_data['ip'] + ':%')).first()
            dicom5_result = db.session.execute('select COUNT(1), SUM(pdu_length) from `a_release_rp` '
                                               'where %s = `send_ip_port` or %s = `receive_ip_port`' % (
                                                   json_data['ip'] + ':%', json_data['ip'] + ':%')).first()
            dicom6_result = db.session.execute('select COUNT(1), SUM(pdu_length) from `a_bort` '
                                               'where %s = `send_ip_port` or %s = `receive_ip_port`' % (
                                                   json_data['ip'] + ':%', json_data['ip'] + ':%')).first()
            dicom7_result = db.session.execute('select COUNT(1), SUM(pdu_length) from `p_data_tf` '
                                               'where %s = `send_ip_port` or %s = `receive_ip_port`' % (
                                                   json_data['ip'] + ':%', json_data['ip'] + ':%')).first()
            db.session.commit()
        except:
            status = cnts.database_error
            message = cnts.database_error_message
    else:
        status = cnts.type_error
        message = cnts.type_error_message
    back_data['status'] = status
    back_data['message'] = message
    return jsonify(back_data)
