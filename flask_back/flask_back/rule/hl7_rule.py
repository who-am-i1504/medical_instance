from flask import (Flask, Request, flash, redirect, jsonify, Blueprint)
from flask_cors import *
from flask_back import db
from flask_back.dao.sql import RuleHl7

bp = Blueprint('rule_hl7', __name__, url_prefix='/rule/hl7')

@bp.route('/add', methods=['POST','GET'])
def hl7_rule_add():
    data = ''
    if Request.method == 'POST':
        json_data = Request.get_json()
        inSql = RuleHl7();
        # inSql.id = json_data['id']
        inSql.value = json_data['value']
        s = db.session.add(inSql)
        print(s)
        s = db.session.commit()
        print(s)
        s = db.session.flush()
        print(s)
        data = inSql
    return jsonify(token=generate_token(data))

@bp.route('/update', methods=['POST'])
def hl7_rule_update():
    return 'HL7 update!'

@bp.route('/get', methods=['POST'])
def hl7_rule_get():

    return ''

