from flask import (request, jsonify, Blueprint,redirect)
from flask_back import db, jsonschema, ValidationError, log
from flask_back.dao.sql import RuleAstm
import flask_back.constant as cnts
from flask_back.constant import RedisHost, RedisPort 
import copy
import redis
import bcrypt
import secrets
import uuid
# import time
reids_pool = redis.ConnectionPool(host=RedisHost, port=RedisPort, decode_responses=True)


def readRole():
    roles = {}
    result = db.session.execute("SELECT `role`,`authority` FROM `role`;")
    db.session.commit()
    result = result.fetchall()
    for role in result:
        roles[role['role']] = role['authority']
    return roles 
Roles = None
C_SALT='$2a$10$IK/.QmdsZQJimvJ2PIaJTe'

bp = Blueprint('user', __name__)

@bp.before_request
def validSession():
    global Roles
    if Roles is None:
        Roles = readRole()
        cnts.Roles = copy.deepcopy(Roles)
    if request.path == '/login' or request.path == '/salt':
        return None
    back = {
        "status":205,
        "message":"您的登录已过期或者您的账号已退出，请先登录。",
        "data":{}
    }
    session=redis.Redis(connection_pool=reids_pool)
    if 'X-Token' in request.headers.keys():
        if session.exists(request.headers['X-Token']):
            if 'update' in request.path or 'add' in request.path or 'delete' in request.path:
                if cnts.validEditor(session.hget(request.headers['X-Token'], 'authority')):
                    return None
                else:
                    back['message'] = '您的权限不足'
                    return jsonify(back)
            return None
    return jsonify(back)

@bp.route('/salt', methods=['GET'])
def generateSalt():
    salt=redis.Redis(connection_pool=reids_pool) 
    back = copy.deepcopy(cnts.back_message)
    current_salt = bcrypt.gensalt(10)
    salt.set(current_salt, request.remote_addr, ex=1800, nx=True)
    back['data'] = current_salt
    return jsonify(back)

@bp.route('/login', methods=['POST'])
@jsonschema.validate('user', 'login')
def login():
    back = {
        'code':0,
        'msg':'登录成功',
        'data':{}
    }
    session=redis.Redis(connection_pool=reids_pool)
    json_data = request.get_json()
    salt=redis.Redis(connection_pool=reids_pool) 
    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))
    if not salt.get(json_data['salt']) == addr:
        salt.delete(json_data['salt'])
        back = {
            'code':500,
            'msg':'请确定您的客户端连接是否正确',
            'data':{}
        }
        return jsonify(back)
    salt.delete(json_data['salt'])
    
    try:

        result = db.session.execute('select * from `user` where `username` = \'%s\';' % json_data['username'])
        
        db.session.commit()
        log.info(cnts.databaseSuccess(addr, path, '`user`'))
        log_tag = False
        back['data'] = {}
        users = result.fetchall()
        for i in users:
            # print(i['password'])
            # print(json_data['password'])
            # print(bcrypt.hashpw(i['password'], ))
            # print('here', bcrypt.checkpw(i['password'].encode('utf-8'), json_data['password'].encode('utf-8')))
            if i['username'] == json_data['username']:
                print(i['username'], bcrypt.checkpw(i['password'].encode('utf-8'), json_data['password'].encode('utf-8')))
                if bcrypt.checkpw(i['password'].encode('utf-8'), json_data['password'].encode('utf-8')):
                    log_tag = True
                    back['data']['username'] = i['username']
                    back['data']['uuid'] = i['uuid']
                    back['data']['authority'] = i['authority']
                    # back['data']['name'] = i['name']
                    # back['data']['name'] = i['name']
                    # back['data']['remote'] = addr
                    sessionId = secrets.token_urlsafe(16)
                    session.hmset(sessionId, back['data'])
                    back['data']['token'] = sessionId
        if not log_tag:
            back['msg'] = '用户名或密码错误',
            back['code'] = 401
        global Roles
        back['data']['roles'] = copy.deepcopy(Roles)
    except Exception as e:
        log.error(cnts.errorLog(addr, path, cnts.database_error_message))
        back['code'] = cnts.database_error
        back['msg'] = cnts.database_error_message
        return jsonify(back)
    
    log.info(cnts.successLog(addr, path))

    return jsonify(back)

@bp.route('/logout', methods=['POST'])
@jsonschema.validate('user', 'logout')
def logout():
    back = copy.deepcopy(cnts.back_message)
    json_data = request.get_json()
    session=redis.Redis(connection_pool=reids_pool)
    session.delete(json_data['token'])
    return jsonify(back)


@bp.route('/user/list', methods=['POST'])
@jsonschema.validate('user', 'list')
def list_users():
    back = copy.deepcopy(cnts.back_message)
    pageSize = cnts.page_size
    sessionid = request.headers['X-Token']
    json_data = request.get_json()
    if 'pageSize' in json_data.keys():
        pageSize = json_data['pageSize']
    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))
    # token 和 UUID 验证，省略
    try:
        session=redis.Redis(connection_pool=reids_pool)
        authority = session.hget(sessionid, 'authority')
        if authority is None:
            back['message'] = '请重新登录'
            back['status'] = 206
            return jsonify(back)
        size = None
        result = None
        # print('HERE')
        if not cnts.validSuperAdmin(authority):
            if not cnts.validAdmin(authority):
                if cnts.validEditorAdmin(authority) and cnts.validReaderAdmin(authority):
                    size = db.session.execute('select COUNT(1) from `user` where `authority` < %d;' % (Roles['ReaderAdmin']))
                    result = db.session.execute('select `username`, `uuid`, `authority` from `user` where `authority` < %d limit %d,%d;' % (Roles['ReaderAdmin'], (json_data['page'] - 1)*pageSize, pageSize))
                elif cnts.validEditorAdmin(authority):
                    size = db.session.execute('select COUNT(1) from `user` where `authority` = %d;' % (Roles['Editor']))
                    result = db.session.execute('select `username`, `uuid`, `authority` from `user` where `authority` = %d limit %d,%d;' % (Roles['Editor'], (json_data['page'] - 1)*pageSize, pageSize))
                elif cnts.validReaderAdmin(authority):
                    size = db.session.execute('select COUNT(1) from `user` where `authority` = %d;' % (Roles['Reader']))
                    result = db.session.execute('select `username`, `uuid`, `authority` from `user` where `authority` = %d limit %d,%d;' % (Roles['Reader'], (json_data['page'] - 1)*pageSize, pageSize))
                else:
                    back['message'] = '权限不足，请找管理员赋予权限'
                    back['status'] = 208
                    return jsonify(back)
            else:
                size = db.session.execute('select COUNT(1) from `user` where `authority` < %d;' % (Roles['Admin']))
                result = db.session.execute('select `username`, `uuid`, `authority` from `user` where `authority` < %d limit %d,%d;' % (Roles['Admin'], (json_data['page'] - 1)*pageSize, pageSize))
        else:
            size = db.session.execute('select COUNT(1) from `user` where `authority` < %d;' % (Roles['SuperAdmin']))
            result = db.session.execute('select `username`, `uuid`, `authority` from `user` where `authority` < %d limit %d,%d;' % (Roles['SuperAdmin'], (json_data['page'] - 1)*pageSize, pageSize))
        
        db.session.commit()
        back['size'] = size.fetchall()[0][0]
        log.info(cnts.databaseSuccess(addr, path, '`user`'))
        
        log_tag = False

        users = result.fetchall()
        back['data'] = []
        for user in users:
            u = {}
            for pro in user.keys():
                u[pro] = user[pro]
            back['data'].append(u)
    except Exception as e:
        
        log.error(cnts.errorLog(addr, path, e))

        back['code'] = cnts.database_error
        back['msg'] = str(e)
        return jsonify(back)
    
    log.info(cnts.successLog(addr, path))

    return jsonify(back)

@bp.route('/user/add', methods=['POST'])
@jsonschema.validate('user', 'userAdd')
def addNewUser():

    back = copy.deepcopy(cnts.back_message)
    pageSize = cnts.page_size
    sessionid = request.headers['X-Token']
    json_data = request.get_json()
    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))
    # token 和 UUID 验证，省略
    try:
        session=redis.Redis(connection_pool=reids_pool)
        authority = session.hget(sessionid, 'authority')
        # print(authority, authority is None)
        if authority is None:
            back['message'] = '请重新登录'
            back['status'] = 206
            return jsonify(back)
        use_authority = json_data['authority']
        if (use_authority & Roles['SuperAdmin']) > 0:
            back['message'] = '您的权限不足'
            back['status'] = 208
            return jsonify(back)
        elif (use_authority & Roles['Admin']) > 0 and not cnts.validSuperAdmin(authority):
            back['message'] = '您的权限不足'
            back['status'] = 208
            return jsonify(back)
        elif ((use_authority & Roles['ReaderAdmin']) > 0 and not cnts.validAdmin(authority)) or (int(authority) & Roles['ReaderAdmin']) == 0:
            back['message'] = '您的权限不足'
            back['status'] = 208
            return jsonify(back)
        elif ((use_authority & Roles['EditorAdmin']) > 0 and not cnts.validAdmin(authority)) or (int(authority) & Roles['EditorAdmin']) == 0:
            back['message'] = '您的权限不足'
            back['status'] = 208
            return jsonify(back)
        elif (use_authority & Roles['Reader']) > 0 and not cnts.validReaderAdmin(authority) or (int(authority) & Roles['Reader']) == 0:
            back['message'] = '您没有读传播权限'
            back['status'] = 208
            return jsonify(back)
        elif (use_authority & Roles['Editor']) > 0 and not cnts.validEditorAdmin(authority) or (int(authority) & Roles['Editor']) == 0:
            back['message'] = '您没有写传播权限不足'
            back['status'] = 208
            return jsonify(back)
        elif use_authority == 0:
            back['message'] = '用户不能没有权限'
            back['status'] = 209
            return jsonify(back)
        uid = ''.join(str(uuid.uuid4()).split("-"))
        size = db.session.execute("SELECT COUNT(1) FROM `user` WHERE `username` = '%s';" % (json_data['username']))
        db.session.commit()
        if size.fetchall()[0][0] > 0:
            back['message'] = '用户名已存在'
            back['status'] = 207
            return jsonify(back)
        result = db.session.execute("insert into `user` (`uuid`, `username`, `password`, `authority`) values('%s', '%s', '%s', %d)" % (uid, json_data['username'], json_data['psd'], use_authority))
        db.session.commit()
    except Exception as e:
        
        log.error(cnts.errorLog(addr, path, e))

        back['status'] = cnts.database_error
        back['message'] = str(e)
        return jsonify(back)
    
    log.info(cnts.successLog(addr, path))

    return jsonify(back)


@bp.route('/user/updateUserName', methods=['POST'])
@jsonschema.validate('user', 'updateUsername')
def updateUsername():

    back = copy.deepcopy(cnts.back_message)
    pageSize = cnts.page_size
    sessionid = request.headers['X-Token']
    json_data = request.get_json()
    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))
    # token 和 UUID 验证，省略
    try:
        session=redis.Redis(connection_pool=reids_pool)
        authority = session.hget(sessionid, 'authority')
        if authority is None:
            back['message'] = '请重新登录'
            back['status'] = 206
            return jsonify(back)
        if not cnts.validAdmin(authority):
            back['message'] = '您的权限不足'
            back['status'] = 208
            return jsonify(back)
        
        # print(authority, authority is None)
        user = db.session.execute("SELECT `username`,`authority` FROM `user` WHERE `uuid` = '%s';" % (json_data['uuid']))
        db.session.commit()
        user = user.fetchall()[0]
        
        use_authority = user['authority']
        if (use_authority & Roles['Admin']) > 0 and not cnts.validSuperAdmin(authority):
            back['message'] = '您的权限不足'
            back['status'] = 207
            return jsonify(back)
        if user['username'] == json_data['username']:
            back['message'] = "新用户名不能与原用户名相同"
            back['status'] = 210
            return jsonify(back)
        result = db.session.execute("update `user` set `username` = '%s' where `uuid` = '%s';" % (json_data['username'], json_data['uuid']))
        db.session.commit()
    except Exception as e:
        
        log.error(cnts.errorLog(addr, path, e))

        back['status'] = cnts.database_error
        back['message'] = str(e)
        return jsonify(back)
    
    log.info(cnts.successLog(addr, path))

    return jsonify(back)

@bp.route('/user/updatePassword', methods=['POST'])
@jsonschema.validate("user", "updatePassword")
def updateUserPsd():

    back = copy.deepcopy(cnts.back_message)
    pageSize = cnts.page_size
    sessionid = request.headers['X-Token']
    json_data = request.get_json()
    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))
    # token 和 UUID 验证，省略
    try:
        session=redis.Redis(connection_pool=reids_pool)
        authority = session.hget(sessionid, 'authority')
        if authority is None:
            back['message'] = '请重新登录'
            back['status'] = 206
            return jsonify(back)
        if not cnts.validAdmin(authority):
            back['message'] = '您的权限不足'
            back['status'] = 208
            return jsonify(back)
        
        # print(authority, authority is None)
        user = db.session.execute("SELECT `password`,`authority` FROM `user` WHERE `uuid` = '%s';" % (json_data['uuid']))
        db.session.commit()
        user = user.fetchall()[0]
        
        use_authority = user['authority']
        if (use_authority & Roles['Admin']) > 0 and not cnts.validSuperAdmin(authority):
            back['message'] = '您的权限不足'
            back['status'] = 207
            return jsonify(back)
        if user['password'] == json_data['psd']:
            back['message'] = "新密码不能与原密码相同"
            back['status'] = 210
            return jsonify(back)
        result = db.session.execute("update `user` set `password` = '%s' where `uuid` = '%s';" % (json_data['psd'], json_data['uuid']))
        db.session.commit()
    except Exception as e:
        
        log.error(cnts.errorLog(addr, path, e))

        back['status'] = cnts.database_error
        back['message'] = str(e)
        return jsonify(back)
    
    log.info(cnts.successLog(addr, path))

    return jsonify(back)

@bp.route('/user/updateAuthority', methods=['POST'])
@jsonschema.validate("user", "updateAuthority")
def updateAuthority():

    back = copy.deepcopy(cnts.back_message)
    pageSize = cnts.page_size
    sessionid = request.headers['X-Token']
    json_data = request.get_json()
    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))
    # token 和 UUID 验证，省略
    try:
        session=redis.Redis(connection_pool=reids_pool)
        authority = session.hget(sessionid, 'authority')
        if authority is None:
            back['message'] = '请重新登录'
            back['status'] = 206
            return jsonify(back)
        if not cnts.validAdmin(authority):
            back['message'] = '您的权限不足'
            back['status'] = 208
            return jsonify(back)
        
        use_authority = json_data['authority']
        if (use_authority & Roles['SuperAdmin']) > 0:
            back['message'] = '您的权限不足'
            back['status'] = 208
            return jsonify(back)
        elif (use_authority & Roles['Admin']) > 0 and not cnts.validSuperAdmin(authority):
            back['message'] = '您的权限不足'
            back['status'] = 208
            return jsonify(back)
        elif ((use_authority & Roles['ReaderAdmin']) > 0 and not cnts.validAdmin(authority)) or (int(authority) & Roles['ReaderAdmin']) == 0:
            back['message'] = '您的权限不足'
            back['status'] = 208
            return jsonify(back)
        elif ((use_authority & Roles['EditorAdmin']) > 0 and not cnts.validAdmin(authority)) or (int(authority) & Roles['EditorAdmin']) == 0:
            back['message'] = '您的权限不足'
            back['status'] = 208
            return jsonify(back)
        elif (use_authority & Roles['Reader']) > 0 and not cnts.validReaderAdmin(authority) or (int(authority) & Roles['Reader']) == 0:
            back['message'] = '您没有读传播权限'
            back['status'] = 208
            return jsonify(back)
        elif (use_authority & Roles['Editor']) > 0 and not cnts.validEditorAdmin(authority) or (int(authority) & Roles['Editor']) == 0:
            back['message'] = '您没有写传播权限不足'
            back['status'] = 208
            return jsonify(back)
        elif use_authority == 0:
            back['message'] = '用户不能没有权限'
            back['status'] = 209
            return jsonify(back)

        # print(authority, authority is None)
        user = db.session.execute("SELECT `authority` FROM `user` WHERE `uuid` = '%s';" % (json_data['uuid']))
        db.session.commit()
        user = user.fetchall()[0]
        
        use_authority = user['authority']
        if (use_authority & Roles['SuperAdmin']) > 0:
            back['message'] = '您的权限不足'
            back['status'] = 208
            return jsonify(back)
        elif (use_authority & Roles['Admin']) > 0 and not cnts.validSuperAdmin(authority):
            back['message'] = '您的权限不足'
            back['status'] = 208
            return jsonify(back)
        elif ((use_authority & Roles['ReaderAdmin']) > 0 and not cnts.validAdmin(authority)) or (int(authority) & Roles['ReaderAdmin']) == 0:
            back['message'] = '您的权限不足'
            back['status'] = 208
            return jsonify(back)
        elif ((use_authority & Roles['EditorAdmin']) > 0 and not cnts.validAdmin(authority)) or (int(authority) & Roles['EditorAdmin']) == 0:
            back['message'] = '您的权限不足'
            back['status'] = 208
            return jsonify(back)
        elif (use_authority & Roles['Reader']) > 0 and not cnts.validReaderAdmin(authority) or (int(authority) & Roles['Reader']) == 0:
            back['message'] = '您没有读传播权限'
            back['status'] = 208
            return jsonify(back)
        elif (use_authority & Roles['Editor']) > 0 and not cnts.validEditorAdmin(authority) or (int(authority) & Roles['Editor']) == 0:
            back['message'] = '您没有写传播权限不足'
            back['status'] = 208
            return jsonify(back)
        elif use_authority == 0:
            back['message'] = '用户不能没有权限'
            back['status'] = 209
            return jsonify(back)
        
        result = db.session.execute("update `user` set `authority` = %d where `uuid` = '%s';" % (json_data['authority'], json_data['uuid']))
        db.session.commit()
    except Exception as e:
        
        log.error(cnts.errorLog(addr, path, e))

        back['status'] = cnts.database_error
        back['message'] = str(e)
        return jsonify(back)
    
    log.info(cnts.successLog(addr, path))

    return jsonify(back)

@bp.route('/user/roles', methods=['POST'])
def getRoles():
    back = copy.deepcopy(cnts.back_message)
    data = copy.deepcopy(Roles)
    session=redis.Redis(connection_pool=reids_pool)
    authority = session.hget(request.headers['X-Token'], 'authority')
    for key in data.keys():
        if (data[key] & int(authority)) == 0:
            data.pop(key, None)
    back['data'] = data
    return jsonify(back)


@bp.route('/changePwd', methods=['POST'])
@jsonschema.validate('user', 'changePwd')
def changePwd():
    back = copy.deepcopy(cnts.back_message)
    addr = request.remote_addr
    path = request.path
    json_data = request.get_json()
    log.info(cnts.requestStart(addr, path, json_data))
    if json_data['oldPsd'] == json_data['newPsd']:
        back['status'] = 204
        back['message'] = '旧密码与新密码不能一样'
        return jsonify(back)
    try:
        session=redis.Redis(connection_pool=reids_pool)
        json_data['username'] = session.hget(request.headers['X-Token'], 'username')
        result = db.session.execute('select * from `user` where `username` = \'%s\';' % (json_data['username']))
        
        db.session.commit()
        log.info(cnts.databaseSuccess(addr, path, '`user`'))
        log_tag = False
        users = result.fetchall()
        for i in users:
            if i['username'] == json_data['username']:
                if i['password'] == json_data['oldPsd']:
                    try:
                        result = db.session.execute("update `user` set `password`='%s' where `username`='%s';" % (json_data['newPsd'], i['username']))
                        db.session.commit()
                        session.delete(request.headers['X-Token'])
                    except:
                        back['status'] = 201
                        back['message'] = '密码更新失败'
                        return jsonify(back)
                    return jsonify(back)
        
        back['status'] = 202
        back['message'] = '旧密码与数据库中密码不一致'

    except:
        log.error(cnts.errorLog(addr, path, cnts.database_error_message))

        back['code'] = cnts.database_error
        back['msg'] = cnts.database_error_message
        return jsonify(back)
        pass
    
    return jsonify(back)


@bp.route('/user/delete', methods=['POST'])
def userDelete():

    



@bp.errorhandler(ValidationError)
def user_error(e):
    log.warning('%s request %s have a error in its request Json  %s' %
                (request.remote_addr, request.path, request.get_json()))
    return jsonify(cnts.params_exception)
