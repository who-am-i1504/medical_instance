from flask import (request, jsonify, Blueprint)
from flask_back import db, jsonschema, ValidationError, log
from flask_back.dao.sql import RuleAstm
import flask_back.constant as cnts
import copy

bp = Blueprint('rule', __name__, url_prefix='/rule')


@bp.route('/get', methods=['POST'])
def get_rule_number():
    back = copy.deepcopy(cnts.back_message)

    addr = request.remote_addr
    path = request.path
    
    try:
        hl7_number = db.session.execute('select count(1) from `rule_hl7`;')
        dicom_number = db.session.execute('select count(1) from `rule_dicom`;')
        astm_number = db.session.execute('select count(1) from `rule_astm`;')

        db.session.commit()
        hl7 = hl7_number.fetchall()
        dicom = dicom_number.fetchall()
        astm = astm_number.fetchall()
        print(hl7, dicom, astm)
        back['data'] = []
        back['data'].append({
            '协议类型':'HL7',
            '数量':hl7[0][0]
        })
        back['data'].append({
            '协议类型':'DICOM',
            '数量':dicom[0][0]
        })
        back['data'].append({
            '协议类型':'ASTM',
            '数量':astm[0][0]
        })

        log.info(cnts.databaseSuccess(addr, path, '`rule_hl7`'))
        log.info(cnts.databaseSuccess(addr, path, '`rule_dicom`'))
        log.info(cnts.databaseSuccess(addr, path, '`rule_astm`'))

        
    except Exception as e:
        
        log.error(cnts.errorLog(addr, path, e))

        back['status'] = cnts.database_error
        back['message'] = cnts.database_error
        return jsonify(back)
    
    log.info(cnts.successLog(addr, path))

    return jsonify(back)


@bp.errorhandler(ValidationError)
def astm_error(e):
    log.warning('%s request %s have a error in its request Json  %s' %
                (request.remote_addr, request.path, request.get_json()))
    return jsonify(cnts.params_exception)
