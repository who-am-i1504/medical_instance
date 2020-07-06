from masscan import PortScanner, PortScannerError, NetworkConnectionError
import ast
import os
config = None
if config is None:
    with open('config/config.cfg', 'r') as f:
        data = f.read().replace('\n', '')
        config = ast.literal_eval(data)

if config is None or 'MaxLen' not in config.keys():
    config={'MaxLen':1000000}

ports_list = None
ports_dic = None
if 'portList' in config.keys():
    ports_list = ''
    ports_dic = config['portList']
    for port in config['portList'].keys():
        if len(ports_list)  == 0:
            ports_list = ports_list + port
        else:
            ports_list = ports_list + ','  + port


def masscan_find(hosts, ports=ports_list, 
    arguments='--max-rate ' + str(config['MaxLen']) + ' --excludefile ' 
    + os.path.join(os.getcwd(), config['ExcludeScanPath'])):
    scanner = None
    if ports is None:
        ports = ports_list
    try:
        scanner = PortScanner()
        if ports is None:
            scanner.scan(hosts=hosts, arguments=arguments, sudo=True)
        else:
            scanner.scan(hosts, ports=ports, arguments=arguments, sudo=True)
    except PortScannerError as error:
        # print(error)
        return error.value
    except NetworkConnectionError as error:
        return {
            'scan':[]
        }
    result = scanner.scan_result
    
    if ports_dic is not None:
        for ip in result['scan'].keys():
            for key in result['scan'][ip].keys():
                for port in result['scan'][ip][key].keys():
                    result['scan'][ip][key][port]['services'] = ports_dic.get(str(port), result['scan'][ip][key][port]['services'])
        pass
    return result


if __name__ == '__main__':
    item = {
        'hosts':'10.246.229.255/31'
    }
    print(masscan_find('10.246.229.255/31'))
