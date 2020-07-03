import copy, datetime
from flask import (request, jsonify, Blueprint)
from flask_back import db, jsonschema, ValidationError, log
import flask_back.constant as cnts
from flask_back.dao.sql import MonitorRule

from .active_find import submitParams

# from .company_ip import qcdata

bp = Blueprint('monitor', __name__, url_prefix='/monitor')

@bp.route('/hl7_by_page', methods=['POST'])
@jsonschema.validate('monitor', 'get')
def monitor_hl7_page():
    back = copy.deepcopy(cnts.back_message)
    page_size = cnts.page_size
    json_data = request.get_json()

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))

    try:
        result = db.session.execute('select count(1) from `message`;')
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`message`'))

        back['size'] = result.fetchall()[0][0]
       
        result = db.session.execute(
            "SELECT main.*, GROUP_CONCAT(DISTINCT seg.`content` ORDER BY seg.`seq` SEPARATOR '\\n') as `content` \
            FROM `message` as main LEFT JOIN `segment` as seg ON main.`id` = seg.`id`\
            GROUP BY main.`id`\
            LIMIT {0},{1};".format((json_data['page'] - 1) * page_size, page_size))
        log.info(cnts.databaseSuccess(addr, path, '`message`'))
        db.session.commit()


        data = result.fetchall()
        back['data'] = []
        if not data == None:
            for i in data:
                a = {}
                for key in i.keys():
                    if 'time' in key and i[key] is not None:
                        a[key] = i[key].strftime('%Y-%m-%d %H:%M:%S')
                    elif 'sender_tag' == key or 'receiver_tag' == key:
                        if i[key] > 0:
                            a[key] = True
                        else:
                            a[key] = False
                    elif key == 'size':
                        a[key] = '{:.2f}'.format(i[key]/1024) + 'KB'
                    else:
                        if i[key] is None or i[key] == '':
                            a[key] = '无'
                        else:
                            a[key] = i[key]
                    # a[key] = i[key]
                back['data'].append(a)
    except Exception as e:
        back['message'] = cnts.database_error_message
        back['status'] = cnts.database_error

        log.error(cnts.errorLog(addr, path, 'database'))

        return jsonify(back)

    back['page'] = json_data['page']

    log.info(cnts.successLog(addr, path))

    return jsonify(back)

@bp.route('/hl7_by_id', methods=['POST'])
@jsonschema.validate('monitor', 'getOne')
def monitor_hl7_id():
    back = copy.deepcopy(cnts.back_message)
    page_size = cnts.page_size
    json_data = request.get_json()

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))

    try:
        result = db.session.execute(
            "SELECT main.*, GROUP_CONCAT(DISTINCT seg.`content` ORDER BY seg.`seq` SEPARATOR '\\n') as `content`\
            FROM `message` as main LEFT JOIN `segment` as seg ON main.`id` = seg.`id`\
            WHERE main.`id` = %d\
            GROUP BY main.`id`;" % json_data['id'])
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`message`'))

        data = result.fetchall()
        back['data'] = {}
        if not data is None and len(data) > 0:
            data = data[0]
            # for i in data:
            for j in data.keys():
                if 'time' in j and data[j] is not None:
                    back['data'][j] = data[j].strftime('%Y-%m-%d %H:%M:%S')
                elif 'sender_tag' == j or 'receiver_tag' == j:
                    if data[j] > 0:
                        back['data'][j] = True
                    else:
                        back['data'][j] = False
                elif j == 'size':
                    back['data'][j] = '{:.2f}'.format(data[j]/1024) + 'KB'
                else:
                    if data[j] is None or data[j] == '':
                        back['data'][j] = '无'
                    else:
                        back['data'][j] = data[j]
                # back['data'][j] = data[j]
    except:
        back['message'] = cnts.database_error_message
        back['status'] = cnts.database_error
        log.error(cnts.errorLog(addr, path, 'database'))

        return jsonify(back)

    # back['page'] = json_data['page']

    log.info(cnts.successLog(addr, path))

    return jsonify(back)


@bp.route('/astm_by_page', methods=['POST'])
@jsonschema.validate('monitor', 'get')
def monitor_astm_page():
    back = copy.deepcopy(cnts.back_message)
    page_size = cnts.page_size
    json_data = request.get_json()

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))

    try:
        result = db.session.execute('select count(1) from `astm_main`;')
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`astm_main`'))

        back['size'] = result.fetchall()[0][0]
        result = db.session.execute(
            "SELECT main.*, GROUP_CONCAT(DISTINCT seg.`content` ORDER BY seg.`id` SEPARATOR '\\n') as `content` \
            FROM `astm_main` as main LEFT JOIN `astm_record` as seg ON main.`id` = seg.`main_id`\
            GROUP BY main.`id`\
            LIMIT %d,%d;" % ((json_data['page'] - 1) * page_size, page_size))
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`astm_main`'))

        data = result.fetchall()
        back['data'] = []
        if not data == None:
            for i in data:
                a = {}
                for key in i.keys():
                    if 'time' in key and i[key] is not None:
                        a[key] = i[key].strftime('%Y-%m-%d %H:%M:%S')
                    elif 'sender_tag' == key or 'receiver_tag' == key:
                        if i[key] > 0:
                            a[key] = True
                        else:
                            a[key] = False
                    elif key == 'size':
                        a[key] = '{:.2f}'.format(i[key]/1024) + 'KB'
                    else:
                        if i[key] is None or i[key] == '':
                            a[key] = '无'
                        else:
                            a[key] = i[key]
                    # a[key] = i[key]
                back['data'].append(a)
    except:
        back['message'] = cnts.database_error_message
        back['status'] = cnts.database_error

        log.info(cnts.errorLog(addr, path, 'database'))

        return jsonify(back)

    back['page'] = json_data['page']

    log.info(cnts.successLog(addr, path))

    return jsonify(back)

@bp.route('/astm_by_id', methods=['POST'])
@jsonschema.validate('monitor', 'getOne')
def monitor_astm_id():
    back = copy.deepcopy(cnts.back_message)
    page_size = cnts.page_size
    json_data = request.get_json()

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))

    try:
        result = db.session.execute(
            "SELECT main.*, GROUP_CONCAT(DISTINCT seg.`content` ORDER BY seg.`id` SEPARATOR '\\n') as `content`\
            FROM `astm_main` as main LEFT JOIN `astm_record` as seg ON main.`id` = seg.`main_id`\
            WHERE main.`id` = %d\
            GROUP BY main.`id`;" % json_data['id'])
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`astm_main`'))

        data = result.fetchall()
        back['data'] = {}
        if not data is None and len(data) > 0:
            data = data[0]
            # for i in data:
            for j in data.keys():
                if 'time' in j and data[j] is not None:
                    back['data'][j] = data[j].strftime('%Y-%m-%d %H:%M:%S')
                elif 'sender_tag' == j or 'receiver_tag' == j:
                    if data[j] > 0:
                        back['data'][j] = True
                    else:
                        back['data'][j] = False
                elif j == 'size':
                    back['data'][j] = '{:.2f}'.format(data[j]/1024) + 'KB'
                else:
                    if data[j] is None or data[j] == '':
                        back['data'][j] = '无'
                    else:
                        back['data'][j] = data[j]
                # back['data'][j] = data[j]
    except:
        back['message'] = cnts.database_error_message
        back['status'] = cnts.database_error
        log.error(cnts.errorLog(addr, path, 'database'))

        return jsonify(back)

    # back['page'] = json_data['page']

    log.info(cnts.successLog(addr, path))

    return jsonify(back)


@bp.route('/dicom_by_page', methods=['POST'])
@jsonschema.validate('monitor', 'get')
def monitor_dicom_page():
    back = copy.deepcopy(cnts.back_message)
    page_size = cnts.page_size
    json_data = request.get_json()

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))

    try:
        result = db.session.execute('select count(1) from `patient_info`;')
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`patient_info`'))

        back['size'] = result.fetchall()[0][0]

        patient = db.session.execute(
            "SELECT *\
            FROM `patient_info` \
            LIMIT %d,%d;" % ((json_data['page'] - 1) * page_size, page_size))

        log.info(cnts.databaseSuccess(addr, path, '`patient_info`'))


        series = db.session.execute(
            "SELECT *\
            FROM `series_info` \
            LIMIT %d,%d;" % ((json_data['page'] - 1) * page_size, page_size))

        log.info(cnts.databaseSuccess(addr, path, '`patient_info`'))

        study = db.session.execute(
            "SELECT *\
            FROM `study_info` \
            LIMIT %d,%d;" % ((json_data['page'] - 1) * page_size, page_size))

        log.info(cnts.databaseSuccess(addr, path, '`study_info`'))


        image = db.session.execute(
            "SELECT *\
            FROM `image_info` \
            LIMIT %d,%d;" % ((json_data['page'] - 1) * page_size, page_size))

        log.info(cnts.databaseSuccess(addr, path, '`image_info`'))
        
        db.session.commit()
        patient = patient.fetchall()
        series = series.fetchall()
        study = study.fetchall()
        image = image.fetchall()

        back['data'] = []
        for index, p in enumerate(patient):
            a = {}
            for i in p.keys():
                if 'time' in i and p[i] is not None:
                    a[i] = p[i].strftime('%Y-%m-%d %H:%M:%S')
                elif 'sender_tag' == i or 'receiver_tag' == i:
                    if p[i] > 0:
                        a[i] = True
                    else:
                        a[i] = False
                elif i == 'size':
                    a[i] = '{:.2f}'.format(p[i]/1024) + 'KB'
                else:
                    if p[i] is None or p[i] == '':
                        a[i] = '无'
                    else:
                        a[i] = p[i]
                # a[i] = p[i]
            if len(series) > index:
                for i in series[index].keys():
                    if series[index][i] is None or series[index][i] == '':
                        a[i] = '无'
                    else:
                        a[i] = series[index][i]
            if len(study) > index:
                for i in study[index].keys():
                    if study[index][i] is None or study[index][i] == '':
                        a[i] = '无'
                    else:
                        a[i] = study[index][i]
            if len(image) > index:
                for i in image[index].keys():
                    if image[index][i] is None or image[index][i] == '':
                        a[i] = '无'
                    else:
                        a[i] = image[index][i]
            back['data'].append(a)
            # for i in 
    except:
        back['message'] = cnts.database_error_message
        back['status'] = cnts.database_error

        log.info(cnts.errorLog(addr, path, 'database'))

        return jsonify(back)

    back['page'] = json_data['page']

    log.info(cnts.successLog(addr, path))

    return jsonify(back)

@bp.route('/dicom_by_id', methods=['POST'])
@jsonschema.validate('monitor', 'getOne')
def monitor_dicom_id():
    back = copy.deepcopy(cnts.back_message)
    page_size = cnts.page_size
    json_data = request.get_json()

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))

    try:
        patient = db.session.execute(
            "SELECT *\
            FROM `patient_info` \
            WHERE `id` = %d;" % (json_data['id']))

        log.info(cnts.databaseSuccess(addr, path, '`patient_info`'))


        series = db.session.execute(
            "SELECT *\
            FROM `series_info` \
            WHERE `id` = %d;" % (json_data['id']))

        log.info(cnts.databaseSuccess(addr, path, '`patient_info`'))

        study = db.session.execute(
            "SELECT *\
            FROM `study_info` \
            WHERE `id` = %d;" % (json_data['id']))

        log.info(cnts.databaseSuccess(addr, path, '`study_info`'))


        image = db.session.execute(
            "SELECT *\
            FROM `image_info` \
            WHERE `id` = %d;" % (json_data['id']))

        log.info(cnts.databaseSuccess(addr, path, '`image_info`'))
        
        db.session.commit()

        patient = patient.fetchall()
        series = series.fetchall()
        study = study.fetchall()
        image = image.fetchall()

        if not patient is None and len(patient) > 0:
            index = 0
            p = patient[0]
            back['data'] = {}
            for i in p.keys():
                if 'time' in i and p[i] is not None:
                    back['data'][i] = p[i].strftime('%Y-%m-%d %H:%M:%S')
                elif 'sender_tag' == i or 'receiver_tag' == i:
                    if p[i] > 0:
                        back['data'][i] = True
                    else:
                        back['data'][i] = False
                elif i == 'size':
                    back['data'][i] = '{:.2f}'.format(p[i]/1024) + 'KB'
                else:
                    if p[i] is None or p[i] == '':
                        back['data'][i] = '无'
                    else:
                        back['data'][i] = p[i]
            if len(series) > 0:
                for i in series[index].keys():
                    if series[index][i] is None or series[index][i] == '':
                        back['data'][i] = '无'
                    else:
                        back['data'][i] = series[index][i]
            if len(study) > 0:
                for i in study[index].keys():
                    if study[index][i] is None or study[index][i] == '':
                        back['data'][i] = '无'
                    else:
                        back['data'][i] = study[index][i]
            if len(image) > 0:
                for i in image[index].keys():
                    if image[index][i] is None or image[index][i] == '':
                        back['data'][i] = '无'
                    else:
                        back['data'][i] = image[index][i]
    except:
        back['message'] = cnts.database_error_message
        back['status'] = cnts.database_error
        log.error(cnts.errorLog(addr, path, 'database'))

        return jsonify(back)

    # back['page'] = json_data['page']

    log.info(cnts.successLog(addr, path))

    return jsonify(back)


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
        back['data'] = []
        if not data == None:
            for i in data:
                a = {}
                a['id'] = i.id
                a['ip'] = i.ip
                back['data'].append(a)
    except:
        back['message'] = cnts.database_error_message
        back['status'] = cnts.database_error

        log.error(cnts.errorLog(addr, path, 'database'))

        return jsonify(back)

    back['page'] = json_data['page']

    log.info(cnts.successLog(addr, path))

    return jsonify(back)


@bp.route('/rule/getOne', methods=['POST'])
@jsonschema.validate('monitor', 'getOne')
def monitor_getOne():
    back = copy.deepcopy(cnts.back_message)
    page_size = cnts.page_size
    json_data = request.get_json()

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))

    try:

        result = db.session.execute(
            'select * from `monitor_rule` where `id` = %d;' % (json_data['id']))
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`monitor_rule`'))

        data = result.fetchall()
        if not data == None:
            for i in data:
                a = {}
                a['id'] = i.id
                a['ip'] = i.ip
                back['data'] = a
    except:
        back['message'] = cnts.database_error_message
        back['status'] = cnts.database_error

        log.error(cnts.errorLog(addr, path, 'database'))

        return jsonify(back)

    log.info(cnts.successLog(addr, path))

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
        
        log.error(cnts.errorLog(addr, path, 'database'))

        return jsonify(back)

    log.info(cnts.successLog(addr, path))

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

        log.error(cnts.errorLog(addr, path, 'database'))

        return jsonify(back)
    
    log.info(cnts.successLog(addr, path))

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

                log.info(cnts.successLog(addr, path))

                return jsonify(back)
        except:
            back['status'] = cnts.database_error
            back['message'] = cnts.database_error_message

            log.error(cnts.errorLog(addr, path, 'database'))

            return jsonify(back)
    try:
        db.session.execute(
            'delete from `monitor_rule` where `id` = %d;' % (json_data['id']))
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`monitor_result`'))

    except:
        back['status'] = cnts.database_error
        back['message'] = cnts.database_error_message

        log.error(cnts.errorLog(addr, path, 'database'))

        return jsonify(back)
    
    log.info(cnts.successLog(addr, path))

    return jsonify(back)


@bp.route('/rule/get_by_ip', methods=['POST'])
@jsonschema.validate('monitor', 'get_by_ip')
def monitor_get_ip():
    back = copy.deepcopy(cnts.back_message)
    json_data = request.get_json()
    addr = request.remote_addr
    path = request.path
    page_size = cnts.page_size
    log.info(cnts.requestStart(addr, path, json_data))

    if 'pageSize' in json_data.keys():
        page_size = json_data['pageSize']
    try:
        result = db.session.execute('select count(1) from `monitor_rule` where `ip` = \'%s\';' % (json_data['ip']))
        db.session.commit()
        log.info(cnts.databaseSuccess(addr, path, '`monitor_result`'))
        back['size'] = result.fetchall()[0][0]
        # current = MonitorRule.query.filter(MonitorRule.id == json_data['id']).first()
        current = db.session.execute(
            'select * from `monitor_rule` where `ip` = \'%s\' limit %d,%d;' % (json_data['ip'], (json_data['page'] - 1) * page_size, page_size))
        db.session.commit()
        data = current.fetchall()
        log.info(cnts.databaseSuccess(addr, path, '`monitor_result`'))
        back['data'] = []
        if not data == None:
            for i in data:
                a = {}
                for j in i.keys():
                    a[j] = i[j]
                back['data'].append(a)
    except:
        back['status'] = cnts.database_error
        back['message'] = cnts.database_error_message
        log.error(cnts.errorLog(addr, path, 'database'))
        return jsonify(back)
        
    log.info(cnts.successLog(addr, path))
    return jsonify(back)


def getHL7DefaultSize():
    return "SELECT COUNT(1) as `sum_num`, SUM(main.`size`) as `sum_size`, MIN(main.`time`) as `start_time`, MAX(main.`time`) as `end_time`\
        FROM `message` as main\
        WHERE main.`sender_tag` > 0 or main.`receiver_tag` > 0;"

def dealHL7DefaultScript(page, page_size):
    
    return "SELECT main.`id`, main.`size`, main.`send_ip_port`, main.`receiver_ip_port`, GROUP_CONCAT(DISTINCT seg.`content` ORDER BY seg.`seq` SEPARATOR '\\n') as `content`\
        FROM `message` as main LEFT JOIN `segment` as seg ON main.`id` = seg.`id`\
        WHERE main.`sender_tag` > 0 or main.`receiver_tag` > 0\
        GROUP BY main.`id`\
        LIMIT {0},{1};".format((page - 1) * page_size, page_size)
    

def getHL7Size(ip, port = None):
    if port is None:
        return "SELECT COUNT(1) as `sum_num`, SUM(main.`size`) as `sum_size`, MIN(main.`time`) as `start_time`, MAX(main.`time`) as `end_time`\
            FROM `message` as main\
            WHERE main.`send_ip_port` LIKE '{0}:%' or main.`receiver_ip_port` LIKE '{0}:%';".format(ip)
    else:
        return "SELECT COUNT(1) as `sum_num`, SUM(main.`size`) as `sum_size`, MIN(main.`time`) as `start_time`, MAX(main.`time`) as `end_time`\
            FROM `message` as main\
            WHERE main.`send_ip_port` = '{0}:{1}' or main.`receiver_ip_port` = '{0}:{1}';".format(ip, port)

def dealHL7Script(ip, page, page_size, port=None):
    if port is None:
        return "SELECT main.`id`, main.`size`, main.`send_ip_port`, main.`receiver_ip_port`, GROUP_CONCAT(DISTINCT seg.`content` ORDER BY seg.`seq` SEPARATOR '\\n') as `content`\
            FROM `message` as main LEFT JOIN `segment` as seg ON main.`id` = seg.`id`\
            WHERE main.`send_ip_port` LIKE '{0}:%' or main.`receiver_ip_port` LIKE '{0}:%'\
            GROUP BY main.`id`\
            LIMIT {1},{2};".format(ip, (page - 1) * page_size, page_size)
    else:
        return "SELECT main.`id`, main.`size`, main.`send_ip_port`, main.`receiver_ip_port`, GROUP_CONCAT(DISTINCT seg.`content` ORDER BY seg.`seq` SEPARATOR '\\n') as `content`\
            FROM `message` as main LEFT JOIN `segment` as seg ON main.`id` = seg.`id`\
            WHERE main.`send_ip_port` = '{0}:{1}' or main.`receiver_ip_port` = '{0}:{1}'\
            GROUP BY main.`id`\
            LIMIT {2},{3};".format(ip, port, (page - 1) * page_size, page_size)

def getAstmDefaultSize():
    
    return "SELECT COUNT(1) as `sum_num`, SUM(main.`size`) as `sum_size`, MIN(main.`time`) as `start_time`, MAX(main.`time`) as `end_time`\
        FROM `astm_main` as main\
        WHERE main.`sender_tag` > 0 or main.`receiver_tag` > 0;"
   

def dealAstmDefalultScript(page, page_size):
    
    return "SELECT main.`id`, main.`size`, main.`send_ip_port`, main.`receiver_ip_port`, GROUP_CONCAT(DISTINCT seg.`content` ORDER BY seg.`id` SEPARATOR '\\n') as `content`\
        FROM `astm_main` as main LEFT JOIN `astm_record` as seg ON main.`id` = seg.`main_id`\
        WHERE main.`sender_tag` > 0 or main.`receiver_tag` > 0\
        GROUP BY main.`id`\
        LIMIT {0},{1};".format((page - 1) * page_size, page_size)
    

def getAstmSize(ip, port = None):
    if port is None:
        return "SELECT COUNT(1) as `sum_num`, SUM(main.`size`) as `sum_size`, MIN(main.`time`) as `start_time`, MAX(main.`time`) as `end_time`\
            FROM `astm_main` as main\
            WHERE main.`send_ip_port` LIKE '{0}:%' or main.`receiver_ip_port` LIKE '{0}:%';".format(ip)
    else:
        return "SELECT COUNT(1) as `sum_num`, SUM(main.`size`) as `sum_size`, MIN(main.`time`) as `start_time`, MAX(main.`time`) as `end_time`\
            FROM `astm_main` as main\
            WHERE main.`send_ip_port` = '{0}:{1}' or main.`receiver_ip_port` = '{0}:{1}';".format(ip, port)

def dealAstmScript(ip, page, page_size, port=None):
    if port is None:
        return "SELECT main.`id`, main.`size`, main.`send_ip_port`, main.`receiver_ip_port`, GROUP_CONCAT(DISTINCT seg.`content` ORDER BY seg.`id` SEPARATOR '\\n') as `content`\
            FROM `astm_main` as main LEFT JOIN `astm_record` as seg ON main.`id` = seg.`main_id`\
            WHERE main.`send_ip_port` LIKE '{0}:%' or main.`receiver_ip_port` LIKE '{0}:%'\
            GROUP BY main.`id`\
            LIMIT {1},{2};".format(ip, (page - 1) * page_size, page_size)
    else:
        return "SELECT main.`id`, main.`size`, main.`send_ip_port`, main.`receiver_ip_port`, GROUP_CONCAT(DISTINCT seg.`content` ORDER BY seg.`id` SEPARATOR '\\n') as `content`\
            FROM `astm_main` as main LEFT JOIN `astm_record` as seg ON main.`id` = seg.`main_id`\
            WHERE main.`send_ip_port` = '{0}:{1}' or main.`receiver_ip_port` = '{0}:{1}'\
            GROUP BY main.`id`\
            LIMIT {2},{3};".format(ip, port, (page - 1) * page_size, page_size)


def getDICOMDefaultSize():
    
    return "SELECT COUNT(1) as `sum_num`, SUM(main.`size`) as `sum_size`, MIN(main.`time`) as `start_time`, MAX(main.`time`) as `end_time`\
        FROM `patient_info` as main\
        WHERE main.`sender_tag` > 0 or main.`receiver_tag` > 0;"
    

def dealDICOMDefaultScript(page, page_size):
    
    return "SELECT *\
        FROM `patient_info` as main LEFT JOIN `series_info` as series ON main.`id` = series.`id` LEFT JOIN `study_info` as study ON main.`id` = study.`id` LEFT JOIN `image_info` as image ON main.`id` = image.`id`\
        WHERE main.`sender_tag` > 0 or main.`receiver_tag` > 0\
        GROUP BY main.`id`\
        LIMIT {0},{1};".format((page - 1) * page_size, page_size)



def getDICOMSize(ip, port = None):
    if port is None:
        return "SELECT COUNT(1) as `sum_num`, SUM(main.`size`) as `sum_size`, MIN(main.`time`) as `start_time`, MAX(main.`time`) as `end_time`\
            FROM `patient_info` as main\
            WHERE main.`send_ip_port` LIKE '{0}:%' or main.`receiver_ip_port` LIKE '{0}:%';".format(ip)
    else:
        return "SELECT COUNT(1) as `sum_num`, SUM(main.`size`) as `sum_size`, MIN(main.`time`) as `start_time`, MAX(main.`time`) as `end_time`\
            FROM `astm_main` as main\
            WHERE main.`send_ip_port` = '{0}:{1}' or main.`receiver_ip_port` = '{0}:{1}';".format(ip, port)

def dealDICOMScript(ip, page, page_size, port=None):
    if port is None:
        return "SELECT *\
            FROM `patient_info` as main LEFT JOIN `series_info` as series ON main.`id` = series.`id` LEFT JOIN `study_info` as study ON main.`id` = study.`id` LEFT JOIN `image_info` as image ON main.`id` = image.`id`\
            WHERE main.`send_ip_port` LIKE '{0}:%' or main.`receiver_ip_port` LIKE '{0}:%'\
            GROUP BY main.`id`\
            LIMIT {1},{2};".format(ip, (page - 1) * page_size, page_size)
    else:
        return "SELECT *\
            FROM `patient_info` as main LEFT JOIN `series_info` as series ON main.`id` = series.`id` LEFT JOIN `study_info` as study ON main.`id` = study.`id` LEFT JOIN `image_info` as image ON main.`id` = image.`id`\
            WHERE main.`send_ip_port` = '{0}:{1}' or main.`receiver_ip_port` = '{0}:{1}'\
            GROUP BY main.`id`\
            LIMIT {2},{3};".format(ip, port, (page - 1) * page_size, page_size)



@bp.route('/result/hl7', methods=['POST'])
@jsonschema.validate('monitor', 'result_page')
def monitor_hl7_ip():
    back = copy.deepcopy(cnts.back_message)
    json_data = request.get_json()

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))
    page_size = cnts.page_size
    try:
        size = None
        result = None
        if 'ip' not in json_data.keys():
            size = db.session.execute(getHL7DefaultSize())
            log.info(cnts.databaseSuccess(addr, path, '`message`'))
            result = db.session.execute(dealHL7DefaultScript(json_data['page'], page_size))
        elif 'port' in json_data.keys():
            size = db.session.execute(getHL7Size(json_data['ip'], port=json_data['port']))
            log.info(cnts.databaseSuccess(addr, path, '`message`'))
            result = db.session.execute(dealHL7Script(json_data['ip'], json_data['page'], page_size, port=json_data['port']))
        else:
            size = db.session.execute(getHL7Size(json_data['ip']))
            log.info(cnts.databaseSuccess(addr, path, '`message`'))
            db.session.commit()
            result = db.session.execute(dealHL7Script(json_data['ip'], json_data['page'], page_size))
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`message`'))

        if size is None or result is None:
            back['data'] = []
            back['size'] = 0 
            back['hl7_ize'] = '0MB'
            log.info(cnts.successLog(addr, path))
            return jsonify(back)
        size = size.fetchall()
        result = result.fetchall()
        
        if len(size) > 0:
            back['size'] = size[0].sum_num
            if size[0]['sum_size'] is None:
                back['hl7_ize'] = '0MB'
            else:
                back['hl7_size'] = '%.2f'%(size[0]['sum_size']/1024/1024) + 'MB'
            if size[0]['start_time'] is not None:
                back['start_time'] = size[0]['start_time'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                back['start_time'] = size[0]['start_time']
            if size[0]['end_time'] is not None:
                back['end_time'] = size[0]['end_time'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                back['end_time'] = size[0]['end_time']
            back['data'] = []
            for i in result:
                a = {}
                for j in i.keys():
                    if j == 'send_ip_port':
                        a['send_ip_port'] = i[j]
                    elif j == 'receiver_ip_port':
                        a['receiver_ip_port'] = i[j]
                    elif j == 'size':
                        a[j] = '{:.2f}'.format(i[j]/1024) + 'KB'
                    elif j == 'sender_tag' or j == 'receiver_tag':
                        if i[j] > 0:
                            a[j] = True
                        else:
                            a[j] = False
                    else:
                        if 'time' in j and i[j] is not None:
                            a[j] = i[j].strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            a[j] = i[j]
                back['data'].append(a)
    except:
        back['status'] = cnts.database_error
        back['message'] = cnts.database_error_message
        
        log.error(cnts.errorLog(addr, path, 'database'))

        return jsonify(back)
    
    log.info(cnts.successLog(addr, path))

    return jsonify(back)

@bp.route('/result/astm', methods=['POST'])
@jsonschema.validate('monitor', 'result_page')
def monitor_astm_ip():
    back = copy.deepcopy(cnts.back_message)
    json_data = request.get_json()

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))
    page_size = cnts.page_size
    try:
        size = None
        result = None
        if 'ip' not in json_data.keys():
            size = db.session.execute(getAstmDefaultSize())
            log.info(cnts.databaseSuccess(addr, path, '`astm_main`'))
            result = db.session.execute(dealAstmDefalultScript(json_data['page'], page_size))
        elif 'port' in json_data.keys():
            size = db.session.execute(getAstmSize(json_data['ip'], port=json_data['port']))
            log.info(cnts.databaseSuccess(addr, path, '`astm_main`'))
            result = db.session.execute(dealAstmScript(json_data['ip'], json_data['page'], page_size, port=json_data['port']))
        else:
            size = db.session.execute(getAstmSize(json_data['ip']))
            log.info(cnts.databaseSuccess(addr, path, '`astm_main`'))
            result = db.session.execute(dealAstmScript(json_data['ip'], json_data['page'], page_size))
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`astm_main`'))
        
        if size is None or result is None:
            back['data'] = []
            back['size'] = 0
            back['astm_ize'] = '0MB'
            return jsonify(back)
        size = size.fetchall()
        result = result.fetchall()
        if len(size) > 0:
            back['size'] = size[0]['sum_num']
            if size[0]['sum_size'] is None:
                back['astm_size'] = '0MB'
            else:
                back['astm_size'] = '%.2f'%(size[0]['sum_size']/1024/1024) + 'MB'
            if size[0]['start_time'] is not None:
                back['start_time'] = size[0]['start_time'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                back['start_time'] = size[0]['start_time']
            if size[0]['end_time'] is not None:
                back['end_time'] = size[0]['end_time'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                back['end_time'] = size[0]['end_time']
            back['data'] = []
            for i in result:
                a = {}
                for j in i.keys():
                    if j == 'send_ip_port':
                        a['send_ip_port'] = i[j]
                    elif j == 'receiver_ip_port':
                        a['receiver_ip_port'] = i[j]
                    elif j == 'size':
                        a[j] = '{:.2f}'.format(i[j]/1024) + 'KB'
                    elif j == 'sender_tag' or j == 'receiver_tag':
                        if i[j] > 0:
                            a[j] = True
                        else:
                            a[j] = False
                    else:
                        if 'time' in j and i[j] is not None:
                            a[j] = i[j].strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            a[j] = i[j]
                back['data'].append(a)
    except Exception as e:
        back['status'] = cnts.database_error
        back['message'] = cnts.database_error_message
        
        log.error(cnts.errorLog(addr, path, 'database'))

        return jsonify(back)
    
    log.info(cnts.successLog(addr, path))

    return jsonify(back)

@bp.route('/result/dicom', methods=['POST'])
@jsonschema.validate('monitor', 'result_page')
def monitor_dicom_ip():
    back = copy.deepcopy(cnts.back_message)
    json_data = request.get_json()

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))
    page_size = cnts.page_size
    try:
        size = None
        result = None
        if 'ip' not in json_data.keys():
            size = db.session.execute(getDICOMDefaultSize())
            log.info(cnts.databaseSuccess(addr, path, '`message`'))
            result = db.session.execute(dealDICOMDefaultScript(json_data['page'], page_size))
        elif 'port' in json_data.keys():
            size = db.session.execute(getDICOMSize(json_data['ip'], port=json_data['port']))
            log.info(cnts.databaseSuccess(addr, path, '`patient_info`'))
            result = db.session.execute(dealDICOmScript(json_data['ip'], json_data['page'], page_size, port=json_data['port']))
        else:
            size = db.session.execute(getDICOMSize(json_data['ip']))
            log.info(cnts.databaseSuccess(addr, path, '`patient_info`'))
            result = db.session.execute(dealDICOMScript(json_data['ip'], json_data['page'], page_size))
        db.session.commit()

        log.info(cnts.databaseSuccess(addr, path, '`patient_info`'))
        
        if size is None or result is None:
            back['data'] = []
            back['size'] = 0
            back['dicom_size'] = '0MB'
            return jsonify(back)
        size = size.fetchall()
        result = result.fetchall()
        if len(size) > 0:
            back['size'] = size[0]['sum_num']
            if size[0]['sum_size'] is None:
                back['dicom_size'] = '0MB'
            else:
                back['dicom_size'] = '%.2f'%(size[0]['sum_size']/1024/1024) + 'MB'
            if size[0]['start_time'] is not None:
                back['start_time'] = size[0]['start_time'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                back['start_time'] = size[0]['start_time']
            if size[0]['end_time'] is not None:
                back['end_time'] = size[0]['end_time'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                back['end_time'] = size[0]['end_time']
            back['data'] = []
            for i in result:
                a = {}
                b = {}
                a['content'] = b
                for j in i.keys():
                    if j == 'send_ip_port':
                        a['send_ip_port'] = i[j]
                    elif j == 'receiver_ip_port':
                        a['receiver_ip_port'] = i[j]
                    elif j == 'size':
                        a[j] = '{:.2f}'.format(i[j]/1024) + 'KB'
                    elif j == 'sender_tag' or j == 'receiver_tag':
                        if i[j] > 0:
                            a[j] = True
                        else:
                            a[j] = False
                    elif j == 'id':
                        a[j] = i[j]
                    else:
                        if 'time' == j and i[j] is not None:
                            b[j] = i[j].strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            b[j] = i[j]
                back['data'].append(a)
    except Exception as e:
        back['status'] = cnts.database_error
        back['message'] = cnts.database_error_message
        
        log.error(cnts.errorLog(addr, path, 'database'))

        return jsonify(back)
    
    log.info(cnts.successLog(addr, path))

    return jsonify(back)

# @bp.route('/work', methods=['POST'])
# @jsonschema.validate('monitor', 'result_get')
# def monitor_work():
#     back = copy.deepcopy(cnts.back_message)
#     json_data = request.get_json()

#     addr = request.remote_addr
#     path = request.path
#     log.info(cnts.requestStart(addr, path, json_data))

#     try:
#         # sql = 'select * from `monitor_result` where %s'%(json_data['ip'])
#         # db.session.execute(sql)
#         # db.session.commit()
        
#         log.info(cnts.databaseSuccess(addr, path, '`monitor_result`'))

#         back['data'] = []
#         example = {
#             'id': 12,
#             'src_ip': json_data['ip'],
#             'dst_ip': json_data['ip'],
#             'src_port': 8080,
#             'dst_port': 8081,
#             'start_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
#             'content': 'MSH|^~\&||MINDRAY_D-SERIES^00A037009A0053DE^EUI-64||||20190929092150000||ORU^R01^ORU_R01|374|P|2.6|||AL|NE||UNICODE UTF-8|||IHE_PCD_001^IHE PCD^1.3.6.1.4.1.19376.1.6.1.1.1^ISOPID|||^^^Hospital^PI||^^^^^^LPV1||I',
#             'size':'100KB'
#         }
#         back['data'].append(example)
#     except:
#         back['status'] = cnts.database_error
#         back['message'] = cnts.database_error_message
        
#         log.error(cnts.errorLog(addr, path, 'database'))

#         return jsonify(back)
    
#     log.info(cnts.successLog(addr, path))

#     return back





# @bp.route('/result/get', methods=['POST'])
# @jsonschema.validate('monitor', 'result_get')
# def monitor_dicom():
#     back = copy.deepcopy(cnts.back_message)
#     json_data = request.get_json()

#     addr = request.remote_addr
#     path = request.path
#     log.info(cnts.requestStart(addr, path, json_data))

#     try:
#         sql = 'select * from `monitor_rule` where `ip` = "%s";' % (
#             json_data['ip'])
#         current = db.session.execute(sql).fetchall()
#         db.session.commit()

#         log.info(cnts.databaseSuccess(addr, path, '`monitor_result`'))

#         if len(current) == 0:
#             back['status'] = cnts.ip_not_found
#             back['message'] = cnts.ip_not_found_message
#             return jsonify(back)
#         # num1, sum1 = hl7_fliter(json_data['ip'])
#         num1, sum1, num2, sum2 = dicom_fliter(json_data['ip'])
#         back['data'] = {}
#         back['data']['hl7_number'] = str(num1) + '条'
#         back['data']['hl7_size'] = str(float('%.4f' % (sum1/1024/1024))) + 'MB'
#         back['data']['dicom_number'] = str(num2) + '条'
#         back['data']['dicom_size'] = str(float('%.4f' % (sum2/1024/1024))) + 'MB'
#     except:
#         back['status'] = cnts.database_error
#         back['message'] = cnts.database_error_message
        
#         log.error(cnts.errorLog(addr, path, 'database'))

#         return jsonify(back)
    
#     log.info(cnts.successLog(addr, path))

#     return jsonify(back)

# def dicom_fliter(ip):
#     sql = 'select COUNT(1), SUM(size) from `message` where `send_ip_port` like "%s" or `receiver_ip_port` like "%s";' % (
#         ip + ':%', ip + ':%')
#     hl7 = db.session.execute(sql).first()
#     result = []
#     for table in cnts.dicom_tables:
#         sql = 'select COUNT(1), SUM(pdu_length) from %s where `send_ip_port` like "%s" or `receive_ip_port` like "%s";' % (
#             table, ip + ':%', ip + ':%')
#         result.append(db.session.execute(sql).first())
#     db.session.commit()

#     log.info(cnts.databaseSuccess(addr, path, '`monitor_result`'))

#     # print(hl7)
#     num1 = hl7[0]
#     sum1 = hl7[1]
#     number = 0
#     sum = 0
#     for i in result:
#         number += i[0]
#         if i[1] == None:
#             sum += 0
#         else:
#             sum += i[1]
    
#     log.info(cnts.successLog(addr, path))

#     return num1, sum1, number, sum

# @bp.route('/dicom_list', methods=['POST'])
# @jsonschema.validate('monitor', 'result_get')
# def get_dicom_list():
#     back = copy.deepcopy(cnts.back_message)
#     json_data = request.get_json()

#     addr = request.remote_addr
#     path = request.path
#     log.info(cnts.requestStart(addr, path, json_data))

#     try:
#         sql = 'select * from `monitor_rule` where `ip` = "%s";' % (
#             json_data['ip'])
#         current = db.session.execute(sql).fetchall()
#         db.session.commit()

#         log.info(cnts.databaseSuccess(addr, path, '`monitor_result`'))

#         if len(current) == 0:
#             back['status'] = cnts.ip_not_found
#             back['message'] = cnts.ip_not_found_message
#             return jsonify(back)
#         result_list = dicom_list(json_data['ip'])
#     except:
#         back['status'] = cnts.database_error
#         back['message'] = cnts.database_error_message
        
#         log.error(cnts.errorLog(addr, path, 'database'))

#         return jsonify(back)

#     log.info(cnts.successLog(addr, path))

#     return jsonify(back)

# def dicom_list(ip):
#     result = []
#     for table in cnts.dicom_tables:
#         result.append('select `id`, `pdu_length` from `%s` where %s = `send_ip_port` or %s = `receiver_ip_port`;' % (
#             table, ip + ':%', ip + ':%')).fetchall()
    
#     db.session.commit()

#     log.info(cnts.databaseSuccess(addr, path, 'dicom_database'))

#     result_list = []
#     # for

#     return result_list


# def dicom_result(id, pdu_type):
#     result = db.session.execute(
#         'select * from %s whrere `id` = %d' % (cnts.dicom_tables[pdu_type], id))
#     db.session.commit()

#     log.info(cnts.databaseSuccess(addr, path, '`dicom_tables`'))

#     return result.first()

@bp.route('active_find', methods=['POST'])
@jsonschema.validate('monitor', 'active_find')
def active_find():
    json_data = request.get_json()
    json_data['FuncType'] = 'masscan'
    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))
    
    # try:
    #     sql_size = 'select count(1) from `active_result` where (`src_ip` = "%s" and `src_port` = %d) or (`dst_ip` = "%s" and `dst_port` = %d);' % (json_data['ip'], json_data['port'], json_data['ip'], json_data['port'])
    #     size = db.session.execute(sql_size).fetchall()
    #     sql = 'select * from `active_result` where (`src_ip` = "%s" and `src_port` = %d) or (`dst_ip` = "%s" and `dst_port` = %d) limit %d,%d;' % (json_data['ip'], json_data['port'], json_data['ip'], json_data['port'], (json_data['page'] - 1)*page_size, page_size)
    #     result = db.session.execute(sql).fetchall()
    #     db.session.commit()
    #     # print(size)
        
    #     log.info(cnts.databaseSuccess(addr, path, '`monitor_result`'))

    #     if size[0][0] == None:
    #         back['size'] = 0
    #     else:
    #         back['size'] = int(size[0][0])
    #     back['data'] = []
    #     for i in result:
    #         a = {}
    #         a['id'] = i.id
    #         a['src_ip'] = i.src_ip
    #         a['src_port'] = i.src_port
    #         a['dst_ip'] = i.dst_ip
    #         a['dst_port'] = i.dst_port
    #         a['time'] = i.time
    #         back['data'].append(a)
    # except:
    #     back['status'] = cnts.database_error
    #     back['message'] = cnts.database_error_message

    #     log.error(cnts.errorLog(addr, path, 'database'))

    #     return jsonify(back)
    # back['page'] = json_data['page']

    # log.info(cnts.successLog(addr, path))
    
    return jsonify(submitParams(json_data))

@bp.route('active_find_detail', methods=['POST'])
@jsonschema.validate('monitor', 'active_find')
def active_find_detail():
    json_data = request.get_json()
    json_data['FuncType'] = 'nmap'
    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))
    return jsonify(submitParams(json_data))

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
