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

def masscan_find(hosts, ports=None, 
    arguments='--max-rate ' + str(config['MaxLen']) + ' --excludefile ' 
    + os.path.join(os.getcwd(), config['ExcludeScanPath'])):
    scanner = None
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
    return scanner.scan_result


if __name__ == '__main__':
    item = {
        'hosts':'10.246.229.255/31'
    }
    print(masscan_find('10.246.229.255/31'))