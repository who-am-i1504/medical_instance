from flask import (request, jsonify, Blueprint, redirect)
from flask_back import db, jsonschema, ValidationError, log
from flask_back.dao.sql import RuleAstm
import flask_back.constant as cnts
from flask_back.constant import RedisHost, RedisPort, tostring
import copy
import redis
import bcrypt
import secrets
import uuid
import datetime
import json
# import time
reids_pool = redis.ConnectionPool(
    host=RedisHost, port=RedisPort, decode_responses=True)

uLogType = ['upsd', 'apsd', 'new', 'cauth', 'cname']
upsd = 0
apsd = 1
newLog = 2
cauth = 3
cname = 4


def user_log(back, ltype, value, uuid):
    if back['status'] == 200:
        # 写入日志
        db.session.execute(
            "insert into `user_record` values(NULL, '%s', '%s', NOW(), '%s');" % (ltype, value, uuid))
        db.session.commit()
        pass


def readRole():
    roles = {}
    result = db.session.execute("SELECT `role`,`authority` FROM `role`;")
    db.session.commit()
    result = result.fetchall()
    for role in result:
        roles[role['role']] = role['authority']
    return roles


Roles = None
C_SALT = '$2a$10$IK/.QmdsZQJimvJ2PIaJTe'

bp = Blueprint('user', __name__)


@bp.after_request
def record_log(response):

    try:
        session = redis.Redis(connection_pool=reids_pool)
        if 'X-Token' in request.headers.keys():
            sessionid = request.headers['X-Token']
            if session.exists(sessionid) and 'log' not in request.path:
                # print('1')
                req = json.dumps(request.get_json())
                # print('2')
                resp = ''
                if 'get' in request.path or 'list' in request.url or 'salt' in request.url or 'roles' in request.url:
                    resp = '......'
                else:
                    resp = json.dumps(response.get_json())
                    if len(resp) > 100:
                        resp = '......'
                # print('3')
                authority = session.hget(sessionid, 'authority')
                # print('4')
                name = session.hget(sessionid, 'username')
                # print('5')
                uuid = session.hget(sessionid, 'uuid')
                # print('6')
                db.session.execute("INSERT INTO `logs` VALUES(NULL, '%s', '%s', '%s', '%s', NOW(), '%s', '%s', %s);" % (
                    str(request.remote_addr), str(request.path), req, resp, str(uuid), str(name), str(authority)))
                db.session.commit()
    except Exception as e:

        pass
    finally:
        return response


@bp.before_request
def validSession():
    global Roles
    if Roles is None:
        Roles = readRole()
        cnts.Roles = copy.deepcopy(Roles)
    if request.path == '/login' or request.path == '/salt':
        return None
    back = {
        "status": cnts.quit_login,
        "message": cnts.quit_login_message,
        "data": {}
    }
    session = redis.Redis(connection_pool=reids_pool)
    if 'X-Token' in request.headers.keys():
        if session.exists(request.headers['X-Token']):
            # if 'update' in request.path or 'add' in request.path or 'delete' in request.path:
            #     if cnts.validEditor(session.hget(request.headers['X-Token'], 'authority')):
            #         return None
            #     else:
            #         back['message'] = '您的权限不足'
            #         return jsonify(back)
            return None
    return jsonify(back)


@bp.route('/user/log', methods=['POST'])
@jsonschema.validate('user', 'userLog')
def getUserLog():
    back = copy.deepcopy(cnts.back_message)
    sessionid = request.headers['X-Token']
    json_data = request.get_json()
    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))
    # token 和 UUID 验证，省略
    try:
        session = redis.Redis(connection_pool=reids_pool)
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
        user = db.session.execute(
            "SELECT `username`,`authority` FROM `user` WHERE `uuid` = '%s';" % (json_data['uuid']))
        db.session.commit()
        user = user.fetchall()
        if len(user) <= 0:
            back['status'] = 208
            back['message'] = '您的账户不存在'
            return jsonify(back)
        user = user[0]
        use_authority = user['authority']
        if (use_authority & Roles['Admin']) > 0 and not cnts.validSuperAdmin(authority):
            back['message'] = '您的权限不足'
            back['status'] = 207
            return jsonify(back)

        result = db.session.execute(
            "SELECT * FROM `user_record` WHERE `uuid` = '%s' ORDER BY `time`;" % (json_data['uuid']))
        db.session.commit()
        result = result.fetchall()
        back['data'] = []
        for item in result:
            nItem = {}
            nItem['time'] = int(item['time'].timestamp() * 1000)
            nItem['opreation'] = item['opreation']
            if nItem['opreation'] == 'new':
                value = {}
                itemName = ['username', 'password', 'authority']
                i = 0
                for s in item['value'].split('\t'):
                    value[itemName[i]] = s
                    i += 1
                nItem['value'] = value
            else:
                nItem['value'] = item['value']
            back['data'].append(nItem)
            back['now'] = int(datetime.datetime.now().timestamp() * 1000)

    except Exception as e:

        log.error(cnts.errorLog(addr, path, e))

        back['code'] = cnts.database_error
        back['msg'] = str(e)
        return jsonify(back)

    log.info(cnts.successLog(addr, path))

    return jsonify(back)


@bp.route('/salt', methods=['GET'])
def generateSalt():
    salt = redis.Redis(connection_pool=reids_pool)
    back = copy.deepcopy(cnts.back_message)
    current_salt = bcrypt.gensalt(10)
    salt.set(current_salt, request.remote_addr, ex=1800, nx=True)
    back['data'] = current_salt
    return jsonify(back)


@bp.route('/login', methods=['POST'])
@jsonschema.validate('user', 'login')
def login():
    back = {
        'code': 0,
        'msg': '登录成功',
        'data': {}
    }
    session = redis.Redis(connection_pool=reids_pool)
    json_data = request.get_json()
    salt = redis.Redis(connection_pool=reids_pool)
    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))
    if not salt.get(json_data['salt']) == addr:
        salt.delete(json_data['salt'])
        back = {
            'code': 500,
            'msg': '请确定您的客户端连接是否正确',
            'data': {}
        }
        return jsonify(back)
    salt.delete(json_data['salt'])

    try:

        result = db.session.execute(
            'select * from `user` where `username` = \'%s\';' % json_data['username'])

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
                # print(i['username'], bcrypt.checkpw(i['password'].encode('utf-8'), json_data['password'].encode('utf-8')))
                if bcrypt.checkpw(i['password'].encode('utf-8'), json_data['password'].encode('utf-8')):
                    log_tag = True
                    back['data']['username'] = i['username']
                    back['data']['uuid'] = i['uuid']
                    back['data']['authority'] = i['authority']
                    if i['cert'] is not None:
                        back['data']['cert']=tostring(i['cert'])
                        back['data']['idnum'] = i['idnum']
                        back['data']['attributes'] = i['attributes']
                    else:
                        back['data']['cert']="无"
                        back['data']['idnum'] = "无"
                        back['data']['attributes'] = "无"

                    # back['data']['name'] = i['name']
                    # back['data']['name'] = i['name']
                    # back['data']['remote'] = addr
                    sessionId = secrets.token_urlsafe(16)
                    session.hmset(sessionId, back['data'])
                    session.pexpire(sessionId, 172800000)
                    if session.exists(i['uuid'].encode('utf-8')):
                        session.delete(session.get(i['uuid'].encode('utf-8')))
                    back['data']['token'] = sessionId
                    session.set(i['uuid'].encode('utf-8'),
                                sessionId.encode('utf-8'), ex=172800, nx=True)

        if not log_tag:
            back['msg'] = '用户名或密码错误',
            back['code'] = 401
        global Roles
        back['data']['roles'] = copy.deepcopy(Roles)
    except Exception as e:
        log.error(cnts.errorLog(addr, path, str(e)))
        back['code'] = cnts.database_error
        back['msg'] = str(e)
        return jsonify(back)

    log.info(cnts.successLog(addr, path))
    # print(back)
    return jsonify(back)


@bp.route('/logout', methods=['POST'])
@jsonschema.validate('user', 'logout')
def logout():
    back = copy.deepcopy(cnts.back_message)
    json_data = request.get_json()
    session = redis.Redis(connection_pool=reids_pool)
    uuid = session.hget(json_data['token'], 'uuid')
    session.delete(uuid)
    session.delete(json_data['token'])
    return jsonify(back)


@bp.route('/attribute_policy', methods=['GET'])
def attribute_policys():
    back = copy.deepcopy(cnts.back_message)
    addr = request.remote_addr
    path = request.path
    try:
        result = db.session.execute('SELECT * FROM `attribute_policy`;')
        
        db.session.commit()
        result = result.fetchall()
        back['data'] = {}
        for i in result:
            back['data'][i['owner']] = i['policy']
        log.info(cnts.databaseSuccess(addr, path, '`attribute_policy`'))

    except Exception as e:

        log.error(cnts.errorLog(addr, path, e))

        back['code'] = cnts.database_error
        back['msg'] = str(e)
        return jsonify(back)

    log.info(cnts.successLog(addr, path))

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
        session = redis.Redis(connection_pool=reids_pool)
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
                    size = db.session.execute(
                        'select COUNT(1) from `user` where `authority` < %d or `authority` = 0;' % (Roles['ReaderAdmin']))
                    result = db.session.execute('select `username`, `uuid`, `authority` from `user` where `authority` < %d limit %d,%d;' % (
                        Roles['ReaderAdmin'], (json_data['page'] - 1)*pageSize, pageSize))
                elif cnts.validEditorAdmin(authority):
                    size = db.session.execute(
                        'select COUNT(1) from `user` where `authority` = %d or `authority` = 0;' % (Roles['Editor']))
                    result = db.session.execute('select `username`, `uuid`, `authority` from `user` where `authority` = %d limit %d,%d;' % (
                        Roles['Editor'], (json_data['page'] - 1)*pageSize, pageSize))
                elif cnts.validReaderAdmin(authority):
                    size = db.session.execute(
                        'select COUNT(1) from `user` where `authority` = %d or `authority` = 0;' % (Roles['Reader']))
                    result = db.session.execute('select `username`, `uuid`, `authority` from `user` where `authority` = %d or `authority` = 0 limit %d,%d;' % (
                        Roles['Reader'], (json_data['page'] - 1)*pageSize, pageSize))
                else:
                    back['message'] = '权限不足，请找管理员赋予权限'
                    back['status'] = 208
                    return jsonify(back)
            else:
                size = db.session.execute(
                    'select COUNT(1) from `user` where `authority` < %d;' % (Roles['Admin']))
                result = db.session.execute('select `username`, `uuid`, `authority` from `user` where `authority` < %d limit %d,%d;' % (
                    Roles['Admin'], (json_data['page'] - 1)*pageSize, pageSize))
        else:
            size = db.session.execute(
                'select COUNT(1) from `user` where `authority` < %d;' % (Roles['SuperAdmin']))
            result = db.session.execute('select `username`, `uuid`, `authority` from `user` where `authority` < %d limit %d,%d;' % (
                Roles['SuperAdmin'], (json_data['page'] - 1)*pageSize, pageSize))

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
        session = redis.Redis(connection_pool=reids_pool)
        authority = session.hget(sessionid, 'authority')
        # print(authority, authority is None)
        if authority is None:
            back['message'] = '请重新登录'
            back['status'] = 206
            return jsonify(back)
        use_authority = json_data['authority']
        if (use_authority & Roles['SuperAdmin']) > 0:
            # print('here1')
            back['message'] = '您的权限不足'
            back['status'] = 208
            return jsonify(back)
        elif (use_authority & Roles['Admin']) > 0 and not cnts.validSuperAdmin(authority):
            # print('here2')
            back['message'] = '您的权限不足'
            back['status'] = 208
            return jsonify(back)
        elif ((use_authority & Roles['ReaderAdmin']) > 0 and not cnts.validAdmin(authority)) and (int(authority) & Roles['ReaderAdmin']) == 0:
            # print('here3')
            back['message'] = '您的权限不足'
            back['status'] = 208
            return jsonify(back)
        elif ((use_authority & Roles['EditorAdmin']) > 0 and not cnts.validAdmin(authority)) and (int(authority) & Roles['EditorAdmin']) == 0:
            # print('here4')
            back['message'] = '您的权限不足'
            back['status'] = 208
            return jsonify(back)
        elif (use_authority & Roles['Reader']) > 0 and not cnts.validReaderAdmin(authority) and (int(authority) & Roles['Reader']) == 0:
            # print('here5')
            back['message'] = '您没有读传播权限'
            back['status'] = 208
            return jsonify(back)
        elif (use_authority & Roles['Editor']) > 0 and not cnts.validEditorAdmin(authority) and (int(authority) & Roles['Editor']) == 0:
            # print('here6')
            back['message'] = '您没有写传播权限'
            back['status'] = 208
            return jsonify(back)
        # elif use_authority == 0:
        #     back['message'] = '用户不能没有权限'
        #     back['status'] = 209
        #     return jsonify(back)
        uid = ''.join(str(uuid.uuid4()).split("-"))
        size = db.session.execute(
            "SELECT COUNT(1) FROM `user` WHERE `username` = '%s';" % (json_data['username']))
        db.session.commit()
        if size.fetchall()[0][0] > 0:
            back['message'] = '用户名已存在'
            back['status'] = 207
            return jsonify(back)
        result = db.session.execute("insert into `user` (`uuid`, `username`, `password`, `authority`, `idnum`, `cert`, `attributes`) values('%s', '%s', '%s', %d, null, null, null);" % (
            uid, json_data['username'], json_data['psd'], use_authority))
        db.session.commit()

        user_log(back, uLogType[newLog], "" + json_data['username'] + '\t' +
                 '*' * 10 + json_data['psd'][-4:-1] + '\t' + str(use_authority), uid)

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
        session = redis.Redis(connection_pool=reids_pool)
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
        user = db.session.execute(
            "SELECT `username`,`authority`, `uuid` FROM `user` WHERE `uuid` = '%s';" % (json_data['uuid']))
        db.session.commit()
        user = user.fetchall()
        if len(user) <= 0:
            back['status'] = 208
            back['message'] = '您的账户不存在'
            return jsonify(back)
        user = user[0]
        use_authority = user['authority']
        if (use_authority & Roles['Admin']) > 0 and not cnts.validSuperAdmin(authority):
            back['message'] = '您的权限不足'
            back['status'] = 207
            return jsonify(back)
        if user['username'] == json_data['username']:
            back['message'] = "新用户名不能与原用户名相同"
            back['status'] = 210
            return jsonify(back)
        if session.exists(json_data['uuid']):
            session.delete(session.get(json_data['uuid']))
            session.delete[json_data['uuid']]
        result = db.session.execute("update `user` set `username` = '%s' where `uuid` = '%s';" % (
            json_data['username'], json_data['uuid']))
        db.session.commit()
        user_log(back, uLogType[cname], "" +
                 json_data['username'], user['uuid'])
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
        session = redis.Redis(connection_pool=reids_pool)
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
        user = db.session.execute(
            "SELECT `password`,`authority` FROM `user` WHERE `uuid` = '%s';" % (json_data['uuid']))
        db.session.commit()
        user = user.fetchall()
        if len(user) <= 0:
            back['status'] = 208
            back['message'] = '您的账户不存在'
            return jsonify(back)
        user = user[0]

        use_authority = user['authority']
        if (use_authority & Roles['Admin']) > 0 and not cnts.validSuperAdmin(authority):
            back['message'] = '您的权限不足'
            back['status'] = 207
            return jsonify(back)
        if user['password'] == json_data['psd']:
            back['message'] = "新密码不能与原密码相同"
            back['status'] = 210
            return jsonify(back)
        if session.exists(json_data['uuid']):
            session.delete(session.get(json_data['uuid']))
            session.delete[json_data['uuid']]
        result = db.session.execute("update `user` set `password` = '%s' where `uuid` = '%s';" % (
            json_data['psd'], json_data['uuid']))
        db.session.commit()
        user_log(back, uLogType[apsd], '*' * 10 +
                 json_data['psd'][-4:-1], json_data['uuid'])
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
        session = redis.Redis(connection_pool=reids_pool)
        authority = session.hget(sessionid, 'authority')
        if authority is None:
            back['message'] = '请重新登录'
            back['status'] = 206
            return jsonify(back)
        # if not cnts.validAdmin(authority):
        #     back['message'] = '您的权限不足'
        #     back['status'] = 208
        #     return jsonify(back)

        use_authority = json_data['authority']
        if (use_authority & Roles['SuperAdmin']) > 0:
            back['message'] = '您的权限不足'
            back['status'] = 208
            return jsonify(back)
        elif (use_authority & Roles['Admin']) > 0 and not cnts.validSuperAdmin(authority):
            back['message'] = '您的权限不足'
            back['status'] = 208
            return jsonify(back)
        elif ((use_authority & Roles['ReaderAdmin']) > 0 and not cnts.validAdmin(authority)) and (int(authority) & Roles['ReaderAdmin']) == 0:
            back['message'] = '您的权限不足'
            back['status'] = 208
            return jsonify(back)
        elif ((use_authority & Roles['EditorAdmin']) > 0 and not cnts.validAdmin(authority)) and (int(authority) & Roles['EditorAdmin']) == 0:
            back['message'] = '您的权限不足'
            back['status'] = 208
            return jsonify(back)
        elif (use_authority & Roles['Reader']) > 0 and not cnts.validReaderAdmin(authority) and (int(authority) & Roles['Reader']) == 0:
            back['message'] = '您没有读传播权限'
            back['status'] = 208
            return jsonify(back)
        elif (use_authority & Roles['Editor']) > 0 and not cnts.validEditorAdmin(authority) and (int(authority) & Roles['Editor']) == 0:
            back['message'] = '您没有写传播权限'
            back['status'] = 208
            return jsonify(back)
        # elif use_authority == 0:
        #     back['message'] = '用户不能没有权限'
        #     back['status'] = 209
        #     return jsonify(back)

        # print(authority, authority is None)
        user = db.session.execute(
            "SELECT `authority` FROM `user` WHERE `uuid` = '%s';" % (json_data['uuid']))
        db.session.commit()

        user = user.fetchall()
        if len(user) <= 0:
            back['status'] = 208
            back['message'] = '您的账户不存在'
            return jsonify(back)
        user = user[0]

        use_authority = user['authority']
        if (use_authority & Roles['SuperAdmin']) > 0:
            back['message'] = '您的权限不足'
            back['status'] = 208
            return jsonify(back)
        elif (use_authority & Roles['Admin']) > 0 and not cnts.validSuperAdmin(authority):
            back['message'] = '您的权限不足'
            back['status'] = 208
            return jsonify(back)
        elif ((use_authority & Roles['ReaderAdmin']) > 0 and not cnts.validAdmin(authority)) and (int(authority) & Roles['ReaderAdmin']) == 0:
            back['message'] = '您的权限不足'
            back['status'] = 208
            return jsonify(back)
        elif ((use_authority & Roles['EditorAdmin']) > 0 and not cnts.validAdmin(authority)) and (int(authority) & Roles['EditorAdmin']) == 0:
            back['message'] = '您的权限不足'
            back['status'] = 208
            return jsonify(back)
        elif (use_authority & Roles['Reader']) > 0 and not cnts.validReaderAdmin(authority) and (int(authority) & Roles['Reader']) == 0:
            back['message'] = '您没有读传播权限'
            back['status'] = 208
            return jsonify(back)
        elif (use_authority & Roles['Editor']) > 0 and not cnts.validEditorAdmin(authority) and (int(authority) & Roles['Editor']) == 0:
            back['message'] = '您没有写传播权限不足'
            back['status'] = 208
            return jsonify(back)
        # elif use_authority == 0:
        #     back['message'] = '用户不能没有权限'
        #     back['status'] = 209
        #     return jsonify(back)
        if use_authority == json_data['authority']:
            return jsonify(back)
        if session.exists(json_data['uuid']):
            session.delete(session.get(json_data['uuid']))
            session.delete[json_data['uuid']]
        result = db.session.execute("update `user` set `authority` = %d where `uuid` = '%s';" % (
            json_data['authority'], json_data['uuid']))
        db.session.commit()
        user_log(back, uLogType[cauth], "" +
                 str(json_data['authority']), json_data['uuid'])
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
    session = redis.Redis(connection_pool=reids_pool)
    authority = session.hget(request.headers['X-Token'], 'authority')
    res = {}
    for key in data.keys():
        if (data[key] & int(authority)) == 0:
            pass
        else:
            res[key] = data[key]
    back['data'] = res
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
        session = redis.Redis(connection_pool=reids_pool)
        json_data['username'] = session.hget(
            request.headers['X-Token'], 'username')
        result = db.session.execute(
            'select * from `user` where `username` = \'%s\';' % (json_data['username']))

        db.session.commit()
        log.info(cnts.databaseSuccess(addr, path, '`user`'))
        log_tag = False
        users = result.fetchall()
        for i in users:
            if i['username'] == json_data['username']:
                if i['password'] == json_data['oldPsd']:
                    try:
                        result = db.session.execute("update `user` set `password`='%s' where `username`='%s';" % (
                            json_data['newPsd'], i['username']))
                        db.session.commit()
                        session.delete(request.headers['X-Token'])
                    except:
                        back['status'] = 201
                        back['message'] = '密码更新失败'
                        return jsonify(back)
                    return jsonify(back)

        back['status'] = 202
        back['message'] = '旧密码与数据库中密码不一致'
        user_log(back, uLogType[upsd], '*' * 10 +
                 json_data['newPsd'][-4:-1], users[0]['uuid'])
    except:
        log.error(cnts.errorLog(addr, path, cnts.database_error_message))

        back['code'] = cnts.database_error
        back['msg'] = cnts.database_error_message
        return jsonify(back)
        pass

    return jsonify(back)


@bp.route('/user/delete', methods=['POST'])
def userDelete():
    back = copy.deepcopy(cnts.back_message)
    pageSize = cnts.page_size
    sessionid = request.headers['X-Token']
    json_data = request.get_json()
    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))
    # token 和 UUID 验证，省略
    try:
        session = redis.Redis(connection_pool=reids_pool)
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
        user = db.session.execute(
            "SELECT `password`,`authority` FROM `user` WHERE `uuid` = '%s';" % (json_data['uuid']))
        db.session.commit()
        user = user.fetchall()[0]

        use_authority = user['authority']
        if cnts.validSuperAdmin(use_authority):
            back['message'] = '超级管理员的账户不能删除'
            back['status'] = 207
            return jsonify(back)
        if (use_authority & Roles['Admin']) > 0 and not cnts.validSuperAdmin(authority):
            back['message'] = '您的权限不足'
            back['status'] = 207
            return jsonify(back)
        if session.exists(json_data['uuid']):
            session.delete(session.get(json_data['uuid']))
            session.delete[json_data['uuid']]
        result = db.session.execute(
            "delete from `user` where `uuid` = '%s';" % (json_data['uuid']))
        db.session.execute(
            "delete from `user_record` where `uuid` = '%s';" % (json_data['uuid']))
        db.session.commit()
    except Exception as e:

        log.error(cnts.errorLog(addr, path, e))

        back['status'] = cnts.database_error
        back['message'] = str(e)
        return jsonify(back)

    log.info(cnts.successLog(addr, path))

    return jsonify(back)


@bp.route('/log/get', methods=['POST'])
@jsonschema.validate('user', 'getLog')
def getLog():
    back = copy.deepcopy(cnts.back_message)
    pageSize = cnts.page_size
    sessionid = request.headers['X-Token']
    json_data = request.get_json()
    if 'pageSize' in json_data.keys():
        pageSize = json_data['pageSize']
    addr = request.remote_addr
    path = request.path
    # token 和 UUID 验证，省略
    try:
        session = redis.Redis(connection_pool=reids_pool)
        authority = session.hget(sessionid, 'authority')
        uuid = session.hget(sessionid, 'uuid')
        name = session.hget(sessionid, 'username')
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
                    size = db.session.execute("select COUNT(1) from `logs` where `authority` < %d or `authority` = 0 or (`uuid` = '%s' and `username` = '%s');" % (
                        Roles['ReaderAdmin'], uuid, name))
                    result = db.session.execute("select * from `logs` where `authority` < %d or (`uuid` = '%s' and `username` = '%s') limit %d,%d;" % (
                        Roles['ReaderAdmin'], (json_data['page'] - 1)*pageSize, uuid, name, pageSize))
                elif cnts.validEditorAdmin(authority):
                    size = db.session.execute("select COUNT(1) from `logs` where `authority` = %d or `authority` = 0 or (`uuid` = '%s' and `username` = '%s');" % (
                        Roles['Editor'], uuid, name))
                    result = db.session.execute("select * from `logs` where `authority` = %d or (`uuid` = '%s' and `username` = '%s') limit %d,%d;" % (
                        Roles['Editor'], (json_data['page'] - 1)*pageSize, uuid, name, pageSize))
                elif cnts.validReaderAdmin(authority):
                    size = db.session.execute("select COUNT(1) from `logs` where `authority` = %d or `authority` = 0 or (`uuid` = '%s' and `username` = '%s');" % (
                        Roles['Reader'], uuid, name))
                    result = db.session.execute("select * from `logs` where `authority` = %d or `authority` = 0 or (`uuid` = '%s' and `username` = '%s') limit %d,%d;" % (
                        Roles['Reader'], uuid, name, (json_data['page'] - 1)*pageSize, pageSize))
                else:
                    back['message'] = '权限不足，请找管理员赋予权限'
                    back['status'] = 208
                    return jsonify(back)
            else:
                size = db.session.execute(
                    "select COUNT(1) from `logs` where `authority` < %d or (`uuid` = '%s' and `username` = '%s');" % (Roles['Admin'], uuid, name))
                result = db.session.execute("select * from `logs` where `authority` < %d or (`uuid` = '%s' and `username` = '%s') limit %d,%d;" % (
                    Roles['Admin'], uuid, name, (json_data['page'] - 1)*pageSize, pageSize))
        else:
            size = db.session.execute(
                "select COUNT(1) from `logs` where `authority` < %d or (`uuid` = '%s' and `username` = '%s');" % (Roles['SuperAdmin'], uuid, name))
            result = db.session.execute("select * from `logs` where `authority` < %d or (`uuid` = '%s' and `username` = '%s') limit %d,%d;" % (
                Roles['SuperAdmin'], uuid, name, (json_data['page'] - 1)*pageSize, pageSize))
        db.session.commit()
        back['size'] = size.fetchall()[0][0]
        users = result.fetchall()
        back['data'] = []
        for user in users:
            u = {}
            for pro in user.keys():
                if pro == 'time':
                    u[pro] = user[pro].strftime('%Y-%m-%d')
                else:
                    u[pro] = user[pro]
            back['data'].append(u)
    except Exception as e:
        back['status'] = cnts.database_error
        back['message'] = str(e)
        return jsonify(back)
    return jsonify(back)

@bp.route('/log/delete', methods=['POST'])
@jsonschema.validate('user', 'delete')
def deleteLog():
    back = copy.deepcopy(cnts.back_message)
    pageSize = cnts.page_size
    sessionid = request.headers['X-Token']
    json_data = request.get_json()
    addr = request.remote_addr
    path = request.path
    log.info(cnts.requestStart(addr, path, json_data))
    # token 和 UUID 验证，省略
    try:
        session = redis.Redis(connection_pool=reids_pool)
        authority = session.hget(sessionid, 'authority')
        uuid = session.hget(sessionid, 'uuid')
        name = session.hget(sessionid, 'username')
        if not cnts.validSuperAdmin(authority):
            back['message'] = '您的权限不足'
            back['status'] = 206
            return jsonify(back)
        db.session.execute(
            "delete from `logs` where `id` = '%s';" % (json_data['id']))
        db.session.commit()
    except Exception as e:
        log.error(cnts.errorLog(addr, path, e))
        back['status'] = cnts.database_error
        back['message'] = str(e)
        return jsonify(back)
    log.info(cnts.successLog(addr, path))
    return jsonify(back)


@bp.route('/log/getByUserName', methods=['POST'])
@jsonschema.validate('user', 'getByName')
def getLogByUName():
    back = copy.deepcopy(cnts.back_message)
    pageSize = cnts.page_size
    sessionid = request.headers['X-Token']
    json_data = request.get_json()
    if 'pageSize' in json_data.keys():
        pageSize = json_data['pageSize']
    addr = request.remote_addr
    path = request.path
    # token 和 UUID 验证，省略
    try:
        session = redis.Redis(connection_pool=reids_pool)
        authority = session.hget(sessionid, 'authority')
        uuid = session.hget(sessionid, 'uuid')
        name = session.hget(sessionid, 'username')
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
                    size = db.session.execute("select COUNT(1) from `logs` where `username` = '%s' and (`authority` < %d or `authority` = 0 or (`uuid` = '%s' and `username` = '%s'));" % (
                        json_data['username'], Roles['ReaderAdmin'], uuid, name))
                    result = db.session.execute("select * from `logs` where `username` = '%s' and (`authority` < %d or (`uuid` = '%s' and `username` = '%s')) limit %d,%d;" % (
                        json_data['username'], Roles['ReaderAdmin'], (json_data['page'] - 1)*pageSize, uuid, name, pageSize))
                elif cnts.validEditorAdmin(authority):
                    size = db.session.execute("select COUNT(1) from `logs` where `username` = '%s' and (`authority` = %d or `authority` = 0 or (`uuid` = '%s' and `username` = '%s'));" % (
                        json_data['username'], Roles['Editor'], uuid, name))
                    result = db.session.execute("select * from `logs` where `username` = '%s' and (`authority` = %d or (`uuid` = '%s' and `username` = '%s')) limit %d,%d;" % (
                        json_data['username'], Roles['Editor'], (json_data['page'] - 1)*pageSize, uuid, name, pageSize))
                elif cnts.validReaderAdmin(authority):
                    size = db.session.execute("select COUNT(1) from `logs` where `username` = '%s' and (`authority` = %d or `authority` = 0 or (`uuid` = '%s' and `username` = '%s'));" % (
                        json_data['username'], Roles['Reader'], uuid, name))
                    result = db.session.execute("select * from `logs` where `username` = '%s' and (`authority` = %d or `authority` = 0 or (`uuid` = '%s' and `username` = '%s')) limit %d,%d;" % (
                        json_data['username'], Roles['Reader'], uuid, name, (json_data['page'] - 1)*pageSize, pageSize))
                else:
                    back['message'] = '权限不足，请找管理员赋予权限'
                    back['status'] = 208
                    return jsonify(back)
            else:
                size = db.session.execute(
                    "select COUNT(1) from `logs` where `username` = '%s' and (`authority` < %d or (`uuid` = '%s' and `username` = '%s'));" % (json_data['username'], Roles['Admin'], uuid, name))
                result = db.session.execute("select * from `logs` where `username` = '%s' and (`authority` < %d or (`uuid` = '%s' and `username` = '%s')) limit %d,%d;" % (
                    json_data['username'], Roles['Admin'], uuid, name, (json_data['page'] - 1)*pageSize, pageSize))
        else:
            size = db.session.execute(
                "select COUNT(1) from `logs` where `username` = '%s' and (`authority` < %d or (`uuid` = '%s' and `username` = '%s'));" % (json_data['username'], Roles['SuperAdmin'], uuid, name))
            result = db.session.execute("select * from `logs` where `username` = '%s' and (`authority` < %d or (`uuid` = '%s' and `username` = '%s')) limit %d,%d;" % (
                json_data['username'], Roles['SuperAdmin'], uuid, name, (json_data['page'] - 1)*pageSize, pageSize))
        db.session.commit()
        back['size'] = size.fetchall()[0][0]
        users = result.fetchall()
        back['data'] = []
        for user in users:
            u = {}
            for pro in user.keys():
                if pro == 'time':
                    u[pro] = user[pro].strftime('%Y-%m-%d')
                else:
                    u[pro] = user[pro]
            back['data'].append(u)
    except Exception as e:
        back['status'] = cnts.database_error
        back['message'] = str(e)
        return jsonify(back)
    return jsonify(back)


@bp.route('/log/getByUUID', methods=['POST'])
@jsonschema.validate('user', 'getByUuid')
def getLogByUUID():
    back = copy.deepcopy(cnts.back_message)
    pageSize = cnts.page_size
    sessionid = request.headers['X-Token']
    json_data = request.get_json()
    if 'pageSize' in json_data.keys():
        pageSize = json_data['pageSize']
    addr = request.remote_addr
    path = request.path
    # token 和 UUID 验证，省略
    try:
        session = redis.Redis(connection_pool=reids_pool)
        authority = session.hget(sessionid, 'authority')
        uuid = session.hget(sessionid, 'uuid')
        name = session.hget(sessionid, 'username')
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
                    size = db.session.execute("select COUNT(1) from `logs` where `uuid` = '%s' and (`authority` < %d or `authority` = 0 or (`uuid` = '%s' and `username` = '%s'));" % (
                        json_data['uuid'], Roles['ReaderAdmin'], uuid, name))
                    result = db.session.execute("select * from `logs` where `uuid` = '%s' and (`authority` < %d or (`uuid` = '%s' and `username` = '%s')) limit %d,%d;" % (
                        json_data['uuid'], Roles['ReaderAdmin'], (json_data['page'] - 1)*pageSize, uuid, name, pageSize))
                elif cnts.validEditorAdmin(authority):
                    size = db.session.execute("select COUNT(1) from `logs` where `uuid` = '%s' and (`authority` = %d or `authority` = 0 or (`uuid` = '%s' and `username` = '%s'));" % (
                        json_data['uuid'], Roles['Editor'], uuid, name))
                    result = db.session.execute("select * from `logs` where `uuid` = '%s' and (`authority` = %d or (`uuid` = '%s' and `username` = '%s')) limit %d,%d;" % (
                        json_data['uuid'], Roles['Editor'], (json_data['page'] - 1)*pageSize, uuid, name, pageSize))
                elif cnts.validReaderAdmin(authority):
                    size = db.session.execute("select COUNT(1) from `logs` where `uuid` = '%s' and (`authority` = %d or `authority` = 0 or (`uuid` = '%s' and `username` = '%s'));" % (
                        json_data['uuid'], Roles['Reader'], uuid, name))
                    result = db.session.execute("select * from `logs` where `uuid` = '%s' and (`authority` = %d or `authority` = 0 or (`uuid` = '%s' and `username` = '%s')) limit %d,%d;" % (
                        json_data['uuid'], Roles['Reader'], uuid, name, (json_data['page'] - 1)*pageSize, pageSize))
                else:
                    back['message'] = '权限不足，请找管理员赋予权限'
                    back['status'] = 208
                    return jsonify(back)
            else:
                size = db.session.execute(
                    "select COUNT(1) from `logs` where `uuid` = '%s' and (`authority` < %d or (`uuid` = '%s' and `username` = '%s'));" % (json_data['uuid'], Roles['Admin'], uuid, name))
                result = db.session.execute("select * from `logs` where `uuid` = '%s' and (`authority` < %d or (`uuid` = '%s' and `username` = '%s')) limit %d,%d;" % (
                    json_data['uuid'], Roles['Admin'], uuid, name, (json_data['page'] - 1)*pageSize, pageSize))
        else:
            size = db.session.execute(
                "select COUNT(1) from `logs` where `uuid` = '%s' and (`authority` < %d or (`uuid` = '%s' and `username` = '%s'));" % (json_data['uuid'], Roles['SuperAdmin'], uuid, name))
            result = db.session.execute("select * from `logs` where `uuid` = '%s' and (`authority` < %d or (`uuid` = '%s' and `username` = '%s')) limit %d,%d;" % (
                json_data['uuid'], Roles['SuperAdmin'], uuid, name, (json_data['page'] - 1)*pageSize, pageSize))
        db.session.commit()
        back['size'] = size.fetchall()[0][0]
        users = result.fetchall()
        back['data'] = []
        for user in users:
            u = {}
            for pro in user.keys():
                if pro == 'time':
                    u[pro] = user[pro].strftime('%Y-%m-%d')
                else:
                    u[pro] = user[pro]
            back['data'].append(u)
    except Exception as e:
        back['status'] = cnts.database_error
        back['message'] = str(e)
        return jsonify(back)
    return jsonify(back)


@bp.route('/attributes/get', methods=['POST'])
@jsonschema.validate('user', 'list')
def getUserAttributes():
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
        session = redis.Redis(connection_pool=reids_pool)
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
                    size = db.session.execute(
                        'select COUNT(1) from `user` where `authority` < %d or `authority` = 0;' % (Roles['ReaderAdmin']))
                    result = db.session.execute('select `username`, `uuid`, `attributes` from `user` where `authority` < %d limit %d,%d;' % (
                        Roles['ReaderAdmin'], (json_data['page'] - 1)*pageSize, pageSize))
                elif cnts.validEditorAdmin(authority):
                    size = db.session.execute(
                        'select COUNT(1) from `user` where `authority` = %d or `authority` = 0;' % (Roles['Editor']))
                    result = db.session.execute('select `username`, `uuid`, `attributes` from `user` where `authority` = %d limit %d,%d;' % (
                        Roles['Editor'], (json_data['page'] - 1)*pageSize, pageSize))
                elif cnts.validReaderAdmin(authority):
                    size = db.session.execute(
                        'select COUNT(1) from `user` where `authority` = %d or `authority` = 0;' % (Roles['Reader']))
                    result = db.session.execute('select `username`, `uuid`, `attributes` from `user` where `authority` = %d or `authority` = 0 limit %d,%d;' % (
                        Roles['Reader'], (json_data['page'] - 1)*pageSize, pageSize))
                else:
                    back['message'] = '权限不足，请找管理员赋予权限'
                    back['status'] = 208
                    return jsonify(back)
            else:
                size = db.session.execute(
                    'select COUNT(1) from `user` where `authority` < %d;' % (Roles['Admin']))
                result = db.session.execute('select `username`, `uuid`, `attributes` from `user` where `authority` < %d limit %d,%d;' % (
                    Roles['Admin'], (json_data['page'] - 1)*pageSize, pageSize))
        else:
            size = db.session.execute(
                'select COUNT(1) from `user` where `authority` < %d;' % (Roles['SuperAdmin']))
            result = db.session.execute('select `username`, `uuid`, `attributes` from `user` where `authority` < %d limit %d,%d;' % (
                Roles['SuperAdmin'], (json_data['page'] - 1)*pageSize, pageSize))

        db.session.commit()
        back['size'] = size.fetchall()[0][0]
        log.info(cnts.databaseSuccess(addr, path, '`user`'))

        log_tag = False

        users = result.fetchall()
        back['data'] = []
        for user in users:
            u = {}
            for pro in user.keys():
                if pro == 'cert':
                    continue
                u[pro] = user[pro]
            back['data'].append(u)
    except Exception as e:

        log.error(cnts.errorLog(addr, path, e))

        back['code'] = cnts.database_error
        back['msg'] = str(e)
        return jsonify(back)

    log.info(cnts.successLog(addr, path))

    return jsonify(back)


@bp.errorhandler(ValidationError)
def user_error(e):
    log.warning('%s request %s have a error in its request Json  %s' %
                (request.remote_addr, request.path, request.get_json()))
    return jsonify(cnts.params_exception)
