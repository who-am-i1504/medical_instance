import ast
from base64 import encodestring
import json
import requests
def Ip2Geo(ip):
    res = requests.get("http://pypi.hitwh.net.cn:7788/ip/info?ip=" + ip + "&acc=city")
    return json.loads(res.text)["data"]
Roles = None

page_size = 10

quit_login = 205
quit_login_message = "您的登录已过期或者您的账号已退出，请重新登录。"

ip_not_found = 408
ip_not_found_message = '您给定的ip地址不在黑名单中'

monitor_delete=407
monitor_delete_message = '您的ip属性与数据库中对应ip不符，请刷新。'

params_error = 406
params_error_message = '参数不正确'

status = 200
message = '成功'

database_error = 401
database_error_message = '数据库错误'

type_error = 402
type_error_message = '数据类型不正确'

file_error = 403
file_error_message = '文件传入不正确'

excel_add_error = 405

collect_error = 409
collect_error_message='已有收集任务在运行，请等待当前任务完成'

def excel_add_error_message(error_num, correct_num):
    return "未加入成功%d个，正确加入%d个" % (error_num, correct_num)

back_message = {
    'status': 200,
    'message': 'success' ,
    'data':''
}

params_exception = {
    'status': params_error,
    'message': params_error_message,
    'data':''    
}

dicom_tables = ['`a_associate_rq`', '`a_associate_ac`',
               '`a_associate_rj`', '`p_data_tf`', '`a_release_rq`', '`a_release_rp`', '`a_bort`']

def requestStart(addr, path, inJson):
    return '%s request for %s with params: %s, It is running......' % (addr, path, inJson)

def databaseSuccess(addr, path, database):
    return '%s request for %s, It is Visit DataBase: %s.' % (addr, path, database)

def errorLog(addr, path, error):
    return '%s request for %s It is have a error %s. ' % (addr, path, error)

def successLog(addr, path):
    return '%s request for %s success return message.'%(addr, path)
config = None
if config is None:
    with open('config/config.cfg', 'r') as f:
        data = f.read().replace('\n', '')
        config = ast.literal_eval(data)
RedisHost=config['redis_host']
RedisPort=config['redis_port']
PicturePath = config['PicturePath']
mysqllink = config['mysql_username'] + ':' + config['mysql_password']+'@'+config['mysql_server']
PcapPath = config['PcapPath']
HL7Message = ['id', 'send_ip_port', 'receiver_ip_port', 'complete_status', 'seqnumber', 'size', 'type', 'time', 'version', 'dsc_status']
ASTMMain = ['id', 'delimiter', 'message_id', 'password', 'sender', 'sender_address',
    'type', 'sender_phone', 'sender_character', 'send_ip_port', 'receiver_ip_port', 
    'receiver', 'receiver_id', ]

special_character = {
    '\\r':'\r',
    '\\n': '\n',
    '\\b':'\b',
    '\\a':'\a',
    "\\'":"\'",
    '\\"':'\"',
    '\\\\':'\\',
    '\\f':'\f',
    '\\v':'\v',
    '\\t':'\t',
    '\\x1c':'\x1c'
}


def validReader(authority):
    if (int(authority) & Roles['Reader']) > 0:
        return True
    return False

def validEditor(authority):
    if (int(authority) & Roles['Editor']) > 0:
        return True
    return False

def validCollect(authority):
    if (int(authority) & Roles['Editor']) > 0:
        return True
    return False

def validDownload(authority):
    if (int(authority) & Roles['Editor']) > 0:
        return True
    return False

def validReaderAdmin(authority):
    if (int(authority) & Roles['ReaderAdmin'] ) > 0:
        return True
    return False

def validEditorAdmin(authority):
    if (int(authority) & Roles['EditorAdmin']) > 0:
        return True
    return False
    
# 是否具有读写权限管理赋予能力
def validAdmin(authority):
    if (int(authority) & Roles['Admin']) > 0:
        return True
    return False

# 最高权限用户的标记，该用户的权限不能更改，但是它能更改其他任何用户的权限
def validSuperAdmin(authority):
    if (int(authority) & Roles['SuperAdmin']) > 0:
        return True
    return False

def tostring(data):
    return str(encodestring(data), encoding='utf-8')

def hash2string(data):
    res = {}
    for key in data.keys():
        res[key] = tostring(data[key])
    return res

def array2string(data)->list:
    res = []
    for i in data:
        res.append(tostring(i))
    return res

def transferURevoKey(key):
    res = {}

    res['m'] = key.m
    res['K0'] = tostring(key.K0)
    res['K1'] = tostring(key.K1)
    res['K2'] = tostring(key.K2)
    res['KJ'] = array2string(key.KJ)
    res['Kijx'] = hash2string(key.Kijx)
    res['attributes'] = key.attributes

    return res


def transferARevoKey(key):
    res = {}

    res['aid'] = key.aid
    res['K'] = tostring(key.K)
    res['L'] = tostring(key.L)
    res['R'] = tostring(key.R)
    res['kx'] = hash2string(key.kx)
    res['attributes'] = key.attribute
    return res


# import os
# import time
# log_file_name = 'logger-' + time.strftime('%Y-%m-%d', time.localtime(time.time())) + '.log'

