from nmap import PortScanner, PortScannerError
import ast

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


def nmap_find(hosts, ports=None, arguments=None):
    try:
        if ports is None:
            ports = ports_list
        scanner = PortScanner()
        result = None
        if arguments is None:
            result = scanner.scan(hosts=hosts, ports=ports, sudo=True)
        else:
            result = scanner.scan(hosts=hosts, ports=ports, arguments=arguments, sudo=True)
        return result
    except PortScannerError as error:
        return error.value


if __name__ == '__main__':
    import time
    start = time.time()
    result = nmap_find('10.246.229.255')
    print(time.time() - start)
    print(result)
    # result = nmap_find('111.34.111.62')
    # print(result)