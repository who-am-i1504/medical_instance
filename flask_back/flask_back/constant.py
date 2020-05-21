import ast

page_size = 10

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
PicturePath = config['PicturePath']
mysqllink = config['mysql_username'] + ':' + config['mysql_password']+'@'+config['mysql_server']
# import os
# import time
# log_file_name = 'logger-' + time.strftime('%Y-%m-%d', time.localtime(time.time())) + '.log'

