from flask import (request, jsonify, Blueprint)
from flask_back import db, jsonschema, ValidationError, log
from flask_back.dao.sql import RuleAstm
import flask_back.constant as cnts
import copy

bp = Blueprint('user', __name__)


@bp.route('/login', methods=['POST'])
@jsonschema.validate('user', 'login')
def login():
    back = {
        'code':0,
        'msg':'登录成功',
        'data':{}
    }
    json_data = request.get_json()

    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))
    
    try:
        result = db.session.execute('select * from `user` where `username` = \'%s\';' % json_data['username'])
        
        db.session.commit()
        log.info(cnts.databaseSuccess(addr, path, '`user`'))
        
        log_tag = False

        users = result.fetchall()
        for i in users:
            if i['username'] == json_data['username']:
                if i['password'] == json_data['password']:
                    log_tag = True
                    for j in i.keys():
                        back['data'][j] = i[j]
                    back['data']['token'] = '8dfhassad0asdjwoeiruty'
        if not log_tag:
            back['msg'] = '用户名或密码错误',
            back['code'] = 401,
    except:
        
        log.error(cnts.errorLog(addr, path))

        back['code'] = cnts.database_error
        back['msg'] = cnts.database_error
        return jsonify(back)
    
    log.info(cnts.successLog(addr, path))

    return jsonify(back)


@bp.route('/user/list', methods=['POST'])
@jsonschema.validate('user', 'list')
def list_users():
    back = {

    }
    pageSize = cnts.page_size

    json_data = request.get_json()
    if 'pageSize' in json_data.keys():
        pageSize = json_data['pageSize']
    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))
    # token 和 UUID 验证，省略
    try:
        
        result = db.session.execute('select * from `user` where `username` = \'%s\'' % json_data['username'])
        
        db.session.commit()
        log.info(cnts.databaseSuccess(addr, path, '`user`'))
        
        log_tag = False

        users = result.fetchall()
        for i in users:
            if i['username'] == json_data['username']:
                if i['password'] == json_data['passsword']:
                    log_tag = True
                    for j in i.keys():
                        back['data'][j] = i[j]
                    back['data']['token'] = '8dfhassad0asdjwoeiruty'
        if not log_tag:
            back['msg'] = '用户名或密码错误',
            back['code'] = 401,
    except:
        
        log.error(cnts.errorLog(addr, path))

        back['code'] = cnts.database_error
        back['msg'] = cnts.database_error
        return jsonify(back)
    
    log.info(cnts.successLog(addr, path))

    return jsonify(back)


@bp.errorhandler(ValidationError)
def user_error(e):
    log.warning('%s request %s have a error in its request Json  %s' %
                (request.remote_addr, request.path, request.get_json()))
    return jsonify(cnts.params_exception)
