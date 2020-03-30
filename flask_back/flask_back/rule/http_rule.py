from flask import (request, jsonify, Blueprint)
from flask_back import db
from flask_back.dao.sql import RuleHttp

bp = Blueprint('rule_http', __name__, url_prefix='/rule/http')

@bp.route('/add', methods=['POST'])
def http_rule_add():
    data = None
    status = 200
    message = '成功'
    back_data = {}

    json_data = request.get_json()
    inSql = RuleHttp()
    # inSql.id = 10
    inSql.value = json_data['value']
    try:
        db.session.add(inSql)
        db.session.commit()
        db.session.flush()
        data = inSql
    except:
        status = 401
        message = "数据库错误"
    back_data['status'] = status
    back_data['message'] = message
    back_data['data'] = {}
    if data != None:
        back_data['data']['id'] = data.id
        back_data['data']['value'] = data.value
    return jsonify(back_data)

@bp.route('/update', methods=['POST'])
def http_rule_update():
    status = 200
    message = "成功"
    json_data = request.get_json()
    hl7_update = RuleHttp()
    hl7_update.id = json_data['id']
    hl7_update.value = json_data['value']
    if isinstance(hl7_update.id, int):
        try:
            current = RuleHttp.query.filter(RuleHttp.id == hl7_update.id).first()
            current.value = hl7_update.value
            db.session.commit()
        except:
            message = "数据库错误"
            status = 401
    else:
        message = "传入数据有误"
        status = 402
    back_data = {}
    back_data['status'] = status
    back_data['message'] = message
    return jsonify(back_data)

@bp.route('/get', methods=['POST'])
def http_rule_get():
    page_size = 20
    pageNo = 1
    size = 0
    status = 200
    message = "成功"
    data = None
    json_data = request.get_json()
    if isinstance(json_data['page'], int):
        pageNo = json_data['page']
    try:
        print(15)
        result = db.session.execute('select count(1) from `rule_hl7`;')
        db.session.commit()
        size = result.fetchall()[0][0]
        result = db.session.execute('select * from `rule_hl7` limit %d,%d;'%((pageNo - 1)*page_size, page_size))
        db.session.commit()
        data = result.fetchall()
    except:
        message="数据库错误"
        status = 401
    back_data = {}
    back_data['status'] = status
    back_data['message'] = message
    back_data['data'] = []
    for i in data:
        a = {}
        a['id'] = i[0]
        a['value'] = i[1]
        back_data['data'].append(a)
    back_data['page'] = pageNo
    back_data['size'] = size
    return jsonify(back_data)

