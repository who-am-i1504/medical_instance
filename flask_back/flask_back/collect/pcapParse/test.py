# import reconstructHan as tc
# import packetConstruct as pc
# import dpktConstruct as dc

# if __name__ == "__main__":
    # tc.prase('E:\\29161\\Destop\\medical_instance\\pcap', 'test6.pcap', 'ftp')
    # open('E:\\29161\\Destop\\medical_instance\\pcap\\ftp\\Incomplete_1588867903-0595205-10:2', 'wb+')
    # pc.construct('E:\\29161\\Destop\\medical_instance\\pcap', 'ftp_download.pcap', 'ftp')
    # pc.construct('E:\\29161\\Destop\\medical_instance\\pcap', 'test6.pcap', 'http')
    # dc.construct('E:\\29161\\Destop\\medical_instance\\pcap', 'test6.pcap', 'http')
    # dc.construct('E:\\29161\\Destop\\medical_instance\\pcap', 'test.pcap', 'http')

import os
import sys
from dpkt.ip import IP
from dpkt.tcp import TCP
from dpkt.dpkt import NeedData
from dpkt.pcap import Reader as PReader
from dpkt.ethernet import Ethernet
from socket import inet_ntop
from socket import AF_INET
from threading import Thread
from collections import defaultdict

import dpkt

from nioWrite import NIOWriter 
import time


def inet_to_str(inet):
    """Convert inet object to a string

        Args:
            inet (inet struct): inet network address
        Returns:
            str: Printable/readable IP address
    """
    # First try ipv4 and then ipv6
    try:
        return inet_ntop(AF_INET, inet)
    except ValueError:
        return inet_ntop(AF_INET6, inet)

def construct(absPath, target, typer, filter = False):
    
    i = 0
    f = open(os.path.join(absPath, target), 'rb')
    # DPKT句柄
    pcap_reader = PReader(f)
    # 超时时间戳
    start = time.time()
    for timestamp, pkt in pcap_reader:
        i += 1
        eth = None
        try:
            eth = Ethernet(pkt)
        except NeedData:
            continue
        if not isinstance(eth.data, IP):
            continue
        pkt = eth.data
        if not isinstance(pkt.data, TCP):
            continue
        # if not isinstance(eth.data, TCP):
        #     continue
        # src = inet_to_str(pkt.src)
        # print(i)
        # dst = inet_to_str(pkt.dst)
        # pkt = pkt.data

    print(time.time() - start)

if __name__=='__main__':
    construct('E:\\29161\\Destop\\medical_instance\\pcap', 'http_download.pcap', 'http', filter=True)