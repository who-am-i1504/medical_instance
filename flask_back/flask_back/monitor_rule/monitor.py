import copy, datetime
from flask import (request, jsonify, Blueprint)
from flask_back import db, jsonschema, ValidationError, log
import flask_back.constant as cnts
from flask_back.dao.sql import MonitorRule, MessageMain, AAssociateRQ, AAssociateAC, AAssociateRJ, AReleaseRQ, \
    AReleaseRP, ABort, PDataTF, ActiveResult, ActiveFindIp

bp = Blueprint('monitor', __name__, url_prefix='/monitor')


@bp.route('/rule/get', methods=['POST'])
@jsonschema.validate('monitor', 'get')
def monitor_get():
    back = copy.deepcopy(cnts.back_message)
    page_size = cnts.page_size
    json_data = request.get_json()

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))

    try:
        result = db.session.execute('select count(1) from `monitor_rule`;')
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`monitor_result`'))

        back['size'] = result.fetchall()[0][0]
        result = db.session.execute(
            'select * from `monitor_rule` limit %d,%d;' % ((json_data['page'] - 1) * page_size, page_size))
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`monitor_result`'))

        data = result.fetchall()
        back_data['data'] = []
        if not data == None:
            for i in data:
                a = {}
                a['id'] = i.id
                a['ip'] = i.ip
                back['data'].append(a)
    except:
        back['message'] = cnts.database_error_message
        back['status'] = cnts.database_error
        return jsonify(back)

    back['page'] = json_data['page']
    return jsonify(back)


@bp.route('/rule/add', methods=['POST'])
@jsonschema.validate('monitor', 'add')
def monitor_add():
    back = copy.deepcopy(cnts.back_message)
    json_data = request.get_json()

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))

    insert_item = MonitorRule()
    insert_item.ip = json_data['ip']
    try:
        db.session.add(insert_item)
        db.session.flush()
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`monitor_result`'))

        data = insert_item
        a = {}
        a['id'] = data.id
        a['ip'] = data.ip
        back['data'] = a
    except:
        back['message'] = cnts.database_error_message
        back['status'] = cnts.database_error
        return jsonify(back)

    return jsonify(back)


@bp.route('/rule/update', methods=['POST'])
@jsonschema.validate('monitor', 'update')
def monitor_update():
    back = copy.deepcopy(cnts.back_message)
    json_data = request.get_json()

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))

    update = MonitorRule()
    update.id = json_data['id']
    update.ip = json_data['ip']
    try:
        current = MonitorRule.query.filter(MonitorRule.id == update.id).first()
        current.ip = update.ip
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`monitor_result`'))

    except:
        back['status'] = cnts.database_error
        back['message'] = cnts.database_error_message
        return jsonify(back)
    return jsonify(back)


@bp.route('/rule/delete', methods=['POST'])
@jsonschema.validate('monitor', 'delete')
def monitor_delete():
    back = copy.deepcopy(cnts.back_message)
    json_data = request.get_json()

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))

    if 'ip' in json_data.keys():
        try:
            # current = MonitorRule.query.filter(MonitorRule.id == json_data['id']).first()
            current = db.session.execute(
                'select * from `monitor_rule` where `id` = %d;' % (json_data['id'])).fetchall()
            db.session.commit()

            log.info(cnts.databaseSuccess(addr, path, '`monitor_result`'))

            if len(current) == 0:
                return jsonify(back)
            current = current[0]
            if current.ip != json_data['ip']:
                back['status'] = cnts.monitor_delete
                back['message'] = cnts.monitor_delete_message
                return jsonify(back)
        except:
            back['status'] = cnts.database_error
            back['message'] = cnts.database_error_message
            return jsonify(back)
    try:
        db.session.execute(
            'delete from `monitor_rule` where `id` = %d;' % (json_data['id']))
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`monitor_result`'))

    except:
        back['status'] = cnts.database_error
        back['message'] = cnts.database_error_message

        log.error(cnts.errorLog(addr, path))

        return jsonify(back)
    return jsonify(back)

@bp.route('/work', methods=['POST'])
@jsonschema.validate('monitor', 'result_get')
def monitor_work():
    back = copy.deepcopy(cnts.back_message)
    json_data = request.get_json()

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))

    try:
        # sql = 'select * from `monitor_result` where %s'%(json_data['ip'])
        # db.session.execute(sql)
        # db.session.commit()
        
        log.info(cnts.databaseSuccess(addr, path, '`monitor_result`'))

        back['data'] = []
        example = {
            'id': 12,
            'src_ip': json_data['ip'],
            'dst_ip': json_data['ip'],
            'src_port': 8080,
            'dst_port': 8081,
            'start_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'content': 'MSH|^~\&||MINDRAY_D-SERIES^00A037009A0053DE^EUI-64||||20190929092150000||ORU^R01^ORU_R01|374|P|2.6|||AL|NE||UNICODE UTF-8|||IHE_PCD_001^IHE PCD^1.3.6.1.4.1.19376.1.6.1.1.1^ISOPID|||^^^Hospital^PI||^^^^^^LPV1||I',
            'size':'100KB'
        }
        back['data'].append(example)
    except:
        back['status'] = cnts.database_error
        back['message'] = cnts.database_error_message
        
        log.error(cnts.errorLog(addr, path))

        return jsonify(back)
    return back


@bp.route('/result/get', methods=['POST'])
@jsonschema.validate('monitor', 'result_get')
def monitor_dicom():
    back = copy.deepcopy(cnts.back_message)
    json_data = request.get_json()

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))

    try:
        sql = 'select * from `monitor_rule` where `ip` = "%s";' % (
            json_data['ip'])
        current = db.session.execute(sql).fetchall()
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`monitor_result`'))

        if len(current) == 0:
            back['status'] = cnts.ip_not_found
            back['message'] = cnts.ip_not_found_message
            return jsonify(back)
        # num1, sum1 = hl7_fliter(json_data['ip'])
        num1, sum1, num2, sum2 = dicom_fliter(json_data['ip'])
        back['data'] = {}
        back['data']['hl7_number'] = str(num1) + '条'
        back['data']['hl7_size'] = str(float('%.4f' % (sum1/1024/1024))) + 'MB'
        back['data']['dicom_number'] = str(num2) + '条'
        back['data']['dicom_size'] = str(float('%.4f' % (sum2/1024/1024))) + 'MB'
    except:
        back['status'] = cnts.database_error
        back['message'] = cnts.database_error_message
        
        log.error(cnts.errorLog(addr, path))

        return jsonify(back)
    return jsonify(back)

def dicom_fliter(ip):
    sql = 'select COUNT(1), SUM(size) from `message` where `send_ip_port` like "%s" or `receiver_ip_port` like "%s";' % (
        ip + ':%', ip + ':%')
    hl7 = db.session.execute(sql).first()
    result = []
    for table in cnts.dicom_tables:
        sql = 'select COUNT(1), SUM(pdu_length) from %s where `send_ip_port` like "%s" or `receive_ip_port` like "%s";' % (
            table, ip + ':%', ip + ':%')
        result.append(db.session.execute(sql).first())
    db.session.commit()

    log.info(cnts.databaseSuccess(addr, path, '`monitor_result`'))

    # print(hl7)
    num1 = hl7[0]
    sum1 = hl7[1]
    number = 0
    sum = 0
    for i in result:
        number += i[0]
        if i[1] == None:
            sum += 0
        else:
            sum +=i[1] 
    return num1, sum1, number, sum

@bp.route('/dicom_list', methods=['POST'])
@jsonschema.validate('monitor', 'result_get')
def get_dicom_list():
    back = copy.deepcopy(cnts.back_message)
    json_data = request.get_json()

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))

    try:
        sql = 'select * from `monitor_rule` where `ip` = "%s";' % (
            json_data['ip'])
        current = db.session.execute(sql).fetchall()
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`monitor_result`'))

        if len(current) == 0:
            back['status'] = cnts.ip_not_found
            back['message'] = cnts.ip_not_found_message
            return jsonify(back)
        result_list = dicom_list(json_data['ip'])
    except:
        back['status'] = cnts.database_error
        back['message'] = cnts.database_error_message
        
        log.error(cnts.errorLog(addr, path))

        return jsonify(back)

    return jsonify(back)

def dicom_list(ip):
    result = []
    for table in cnts.dicom_tables:
        result.append('select `id`, `pdu_length` from `%s` where %s = `send_ip_port` or %s = `receiver_ip_port`;' % (
            table, ip + ':%', ip + ':%')).fetchall()
    
    db.session.commit()

    log.info(cnts.databaseSuccess(addr, path, 'dicom_database'))

    result_list = []
    # for

    return result_list


def dicom_result(id, pdu_type):
    result = db.session.execute(
        'select * from %s whrere `id` = %d' % (cnts.dicom_tables[pdu_type], id))
    db.session.commit()

    log.info(cnts.databaseSuccess(addr, path, '`dicom_tables`'))

    return result.first()

@bp.route('active_find', methods=['POST'])
@jsonschema.validate('monitor', 'active_find')
def active_find():
    page_size = 10
    back = copy.deepcopy(cnts.back_message)
    json_data = request.get_json()

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))
    
    try:
        sql_size = 'select count(1) from `active_result` where (`src_ip` = "%s" and `src_port` = %d) or (`dst_ip` = "%s" and `dst_port` = %d);' % (json_data['ip'], json_data['port'], json_data['ip'], json_data['port'])
        size = db.session.execute(sql_size).fetchall()
        sql = 'select * from `active_result` where (`src_ip` = "%s" and `src_port` = %d) or (`dst_ip` = "%s" and `dst_port` = %d) limit %d,%d;' % (json_data['ip'], json_data['port'], json_data['ip'], json_data['port'], (json_data['page'] - 1)*page_size, page_size)
        result = db.session.execute(sql).fetchall()
        db.session.commit()
        # print(size)
        
        log.info(cnts.databaseSuccess(addr, path, '`monitor_result`'))

        if size[0][0] == None:
            back['size'] = 0
        else:
            back['size'] = int(size[0][0])
        back['data'] = []
        for i in result:
            a = {}
            a['id'] = i.id
            a['src_ip'] = i.src_ip
            a['src_port'] = i.src_port
            a['dst_ip'] = i.dst_ip
            a['dst_port'] = i.dst_port
            a['time'] = i.time
            back['data'].append(a)
    except:
        back['status'] = cnts.database_error
        back['message'] = cnts.database_error_message

        log.error(cnts.errorLog(addr, path))

        return jsonify(back)
    back['page'] = json_data['page']
    return jsonify(back)


@bp.errorhandler(ValidationError)
def on_validation_error(e):

    log.warning('%s request %s have a error in its request Json' %
                (request.remote_addr, request.path))

    return jsonify(cnts.params_exception)


# @bp.route('/result', methods=['POST'])
# def monitor_result():
#     status = cnts.status
#     message = cnts.message
#     json_data = request.get_json()
#     back_data = {}
#     if 'ip' not in json_data.keys():
#         back_data['status'] = cnts.params_error
#         back_data['status'] = cnts.params_error_message
#         return jsonify(back_data)
#     if isinstance(json_data['ip'], str):
#         try:
#             current = MonitorRule.query.filter(MonitorRule.ip == json_data['ip']).first()
#             if current is None or 'id' not in current.keys() or current['id'] is None or current['id'] <= 0:
#                 back_data['status'] = cnts.ip_not_found
#                 back_data['message'] = cnts.ip_not_found_message
#                 return jsonify(back_data)
#         except:
#             status = cnts.database_error
#             message = cnts.database_error_message
#         try:
#             hl7_result = db.session.execute('select COUNT(1), SUM(size) from `message` '
#                                             'where %s = `send_ip_port` or %s = `receive_ip_port`' % (
#                                                 json_data['ip'] + ':%', json_data['ip'] + ':%')).first()
#             dicom1_result = db.session.execute('select COUNT(1), SUM(pdu_length) from `a_associate_rq` '
#                                                'where %s = `send_ip_port` or %s = `receive_ip_port`'
#                                                % (json_data['ip'] + ':%', json_data['ip'] + ':%')).first()
#             dicom2_result = db.session.execute('select COUNT(1), SUM(pdu_length) from `a_associate_ac` '
#                                                'where %s = `send_ip_port` or %s = `receive_ip_port`' % (
#                                                    json_data['ip'] + ':%', json_data['ip'] + ':%')).first()
#             dicom3_result = db.session.execute('select COUNT(1), SUM(pdu_length) from `a_associate_rj` '
#                                                'where %s = `send_ip_port` or %s = `receive_ip_port`' % (
#                                                    json_data['ip'] + ':%', json_data['ip'] + ':%')).first()
#             dicom4_result = db.session.execute('select COUNT(1), SUM(pdu_length) from `a_release_rq` '
#                                                'where %s = `send_ip_port` or %s = `receive_ip_port`' % (
#                                                    json_data['ip'] + ':%', json_data['ip'] + ':%')).first()
#             dicom5_result = db.session.execute('select COUNT(1), SUM(pdu_length) from `a_release_rp` '
#                                                'where %s = `send_ip_port` or %s = `receive_ip_port`' % (
#                                                    json_data['ip'] + ':%', json_data['ip'] + ':%')).first()
#             dicom6_result = db.session.execute('select COUNT(1), SUM(pdu_length) from `a_bort` '
#                                                'where %s = `send_ip_port` or %s = `receive_ip_port`' % (
#                                                    json_data['ip'] + ':%', json_data['ip'] + ':%')).first()
#             dicom7_result = db.session.execute('select COUNT(1), SUM(pdu_length) from `p_data_tf` '
#                                                'where %s = `send_ip_port` or %s = `receive_ip_port`' % (
#                                                    json_data['ip'] + ':%', json_data['ip'] + ':%')).first()
#             db.session.commit()
#         except:
#             status = cnts.database_error
#             message = cnts.database_error_message
#     else:
#         status = cnts.type_error
#         message = cnts.type_error_message
#     back_data['status'] = status
#     back_data['message'] = message
#     return jsonify(back_data)
