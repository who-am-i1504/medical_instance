
page_size = 8

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
