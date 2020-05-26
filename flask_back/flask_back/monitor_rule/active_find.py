
from .masscan_find import masscan_find
from .nmap_find import nmap_find
import ast
import flask_back.constant as cnts
import copy
config = None
if config is None:
    with open('config/config.cfg', 'r') as f:
        data = f.read().replace('\n', '')
        config = ast.literal_eval(data)

if config is None or 'ThresHoldMasscanOrNmap' not in config.keys():
    config={'ThresHoldMasscanOrNmap':31}

def submitParams(item):
    back = copy.deepcopy(cnts.back_message)
    hosts = item['hosts']
    FuncType = ''
    if 'FuncType' in item.keys():
        FuncType = item['FuncType']
    if FuncType == 'nmap' or (FuncType=='' and (hosts.find('/') < 0 or int(hosts[hosts.find('/') + 1:]) >= config['ThresHoldMasscanOrNmap'])):
        # 选用nmap探测
        # print('use nmap!')
        ports = None
        if 'ports' in item.keys():
            ports = item['ports']
        result = nmap_find(item['hosts'], ports=ports, arguments='-sT')
        if isinstance(result, dict):
            back['data'] = result['scan']
            return back
        back['data'] = result
        return back
        pass
    else:
        ports = None
        if 'ports' in item.keys():
            ports = item['ports']
        result = masscan_find(item['hosts'], ports=ports)
        if isinstance(result, dict):
            back['data'] = result['scan']
            return back
        back['data'] = '因为扫描一些IP可能会被请去喝茶，因此有白名单来避免此类情况，所以有可能出现以下情况：\n' + result
        # back['data'] = ''
        return back

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.WARNING)
    import time
    start = time.time()
    item = {
        'hosts':'10.246.229.255/31'
        # 'FuncType':'masscan'
    }
    result = submitParams(item)
    print(result)
    print(time.time()-start)

