from nmap import PortScanner, PortScannerError

def nmap_find(hosts, ports=None, arguments=None):
    try:
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