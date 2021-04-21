import os
import sys
from dpkt.ip import IP
from dpkt.tcp import TCP
from .HttpPacket import Response
from dpkt.pcap import Reader as PReader
from dpkt.ethernet import Ethernet
from socket import inet_ntop
from socket import AF_INET
import socket
from threading import Thread
from collections import defaultdict
from dpkt.dpkt import NeedData, UnpackError
from pydicom.errors import InvalidDicomError
import dpkt
import time
from .nioWrite import NIOWriter 
import re


pattern = re.compile(r'^H\|[\\|\^|&|~]{3,5}')

# 一些提前定义的变量
LengthTag = 1000

# 各种预先定义的位置
# 前一个key
head = 0
# 后一个key
after = 1
# 源地址端口
srcPort = 2
# 目的地址端口
dstPort = 3
# 时间戳 （用于超时判定，非常规超时判断）
timeTag = 4
# 文件名称，用于数据量过大时追加文件
fileTag = 5
# 内容开始位置
chunked = 6
content = 7

# 用于超时的时间限制
# 即每隔多长时间检查一次字典中的无效数据
TimeThreshold = 1


def WriteFile(dic, value, pkt, key1, key2, writer, absPath, typer, src, dst):
    key3 = dst + ':' + str(pkt.dport) + '-'  + src + ':' + str(pkt.sport) +  '_' + str(pkt.ack)
    Another = dic.pop(key3, None)
    if not Another is None:
        if key3 == Another[head]:
            dic.pop(Another[after], None)
        else:
            dic.pop(Another[head], None)
        dic.pop(dst + ':' + str(pkt.dport) + '-'  + src + ':' + str(pkt.sport), None)
        item = {}
        item['fileName'] = 'Y_%s' % (Another[fileTag])
        item['absPath'] = os.path.join(absPath, typer)
        item['data']=Another[content:]
        writer.put(item)
    item1 = {}
    item1['fileName'] = 'Y_%s' % (value[fileTag])
    item1['absPath'] = os.path.join(absPath, typer)  
    item1['data'] = value[content:]
    writer.put(item1)

def WriteFileOnly(writer, value, absPath, typer):
    item = {}
    item['fileName'] = 'Y_%s' % (value[fileTag])
    item['absPath'] = os.path.join(absPath, typer)
    item['data'] = value[content:]
    writer.put(item)
    return value[0 : content]

def judgeDcm(data):
    if len(data) >= 132 and data[128:132] == b'DICM':
        return True
    return False

def judgeAstm(data):
    if re.match(b'H\\|[\\\|\\^|&|~]{3,5}', data):
        return True
    return False

def inet_to_str(inet):
    """Convert inet object to a string

        Args:
            inet (inet struct): inet network address
        Returns:
            str: Printable/readable IP address
    """
    # First try ipv4 and then ipv6
    try:
        return socket.inet_ntop(socket.AF_INET, inet)
    except ValueError:
        return socket.inet_ntop(socket.AF_INET6, inet)

def construct(absPath, target, typer, filter = True):
    # 建立目标存储文件夹
    if not os.path.exists(os.path.join(absPath, typer)):
        os.mkdir(os.path.join(absPath, typer))
    # 初始化异步写对象
    writer = NIOWriter()
    # 启动写线程，避免写IO影响数据包处理速度
    t = Thread(target=writer.start_loop)
    t.start()
    time.sleep(1)
    dic = defaultdict(None)
    i = 0
    #读取数据包
    f = open(os.path.join(absPath, target), 'rb')
    # DPKT句柄
    pcap_reader = PReader(f)
    # 超时时间戳
    start = time.time()
    # 记录开始时间
    # allTime = start
    # 迭代读取数据包
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
        src = inet_to_str(pkt.src)
        dst = inet_to_str(pkt.dst)
        pkt = pkt.data

        # i += 1
        now = time.time()
        if now - start >= TimeThreshold:
            for key in list(dic.keys()):
                if not key in dic:
                    continue
                value = dic[key]
                if (now - value[timeTag]) >= TimeThreshold:
                    dic.pop(value[head], None)
                    dic.pop(value[after], None)
            # 更新数据
            start = time.time()
       
        # 对pkt进行相应的处理
        seq = pkt.seq + len(pkt.data)
        
        if (pkt.flags & 2) == 2:
            seq += 1
        
        # HTTP对于乱序流的处理需要定位
        key = src + ':' + str(pkt.sport) + '-' + dst + ':' + str(pkt.dport)
        # 用于寻找特定的前序流
        key1 = src + ':' + str(pkt.sport) + '-' + dst + ':' + str(pkt.dport) + '_' + str(pkt.seq)
        # 用于查找后续流
        key2 = src + ':' + str(pkt.sport) + '-' + dst + ':' + str(pkt.dport) + '_' + str(seq)
        value = dic.pop(key1, None)
        
        if not value is None:
            # 追加
            if key1 == value[head] and value[head] != value[after]:
                # 重传数据包
                # 略过
                continue
            # 非重传数据包
            
            # HTTP 数据特殊处理
            try:
                http = Response(pkt.data)
                dic.pop(value[head], None)
                dic.pop(value[after], None)
                dic.pop(key, None)
                WriteFile(dic, value, pkt, key1, key2, writer, absPath, typer, src, dst)
                value = value[0:content]
                chunked_tag = False
                if http.headers.get('transfer-encoding', '').lower() == 'chunked':
                    chunked_tag = True
                if judgeDcm(http.body):# DICM文件判断逻辑
                    # dcm文件存储
                    value[fileTag] = str(time.time()) + '_' + src + '-' + str(pkt.sport) +'_'+ dst + '-' + str(pkt.dport) + '.dcm'
                    value[timeTag] = time.time()
                    value[chunked] = chunked_tag
                    value.append(http.body)
                    dic[key] = value
                    dic[key1] = value
                    dic[key2] = value
                    pass
                elif judgeAstm(http.body):# ASTM文件判断逻辑
                    # astm 文件存储
                    value[fileTag] = str(time.time()) + '_' + src + '-' + str(pkt.sport) +'_'+ dst + '-' + str(pkt.dport) + '.astm'
                    value[timeTag] = time.time()
                    value[chunked] = chunked_tag
                    value.append(http.body)
                    dic[key] = value
                    dic[key1] = value
                    dic[key2] = value
                elif filter:
                    value[fileTag] = str(time.time()) + '_' + src + '-' + str(pkt.sport) +'_'+ dst + '-' + str(pkt.dport) + '.unknow'
                    value[timeTag] = time.time()
                    value[chunked] = chunked_tag
                    value.append(http.body)
                    dic[key] = value
                    dic[key1] = value
                    dic[key2] = value
                    pass
                continue
            except NeedData:
                pass
            except UnpackError:
                pass

            value.append(pkt.data)
            # 测试代码
            # if i == 121:
            #     print(pkt, pkt['TCP'].flags, pkt['TCP'].flags & 1)
            # 测试代码结束

            if (pkt.flags & 1) == 1:
                # 清除键值
                dic.pop(value[head], None)
                dic.pop(value[after], None)
                dic.pop(key, None)
                WriteFile(dic, value, pkt, key1, key2, writer, absPath, typer, src, dst)
                # if not dic.pop(key1, None) is None:
                #     print('here')
                continue
 
            # 乱序数据包
            while True:
                current = dic.pop(key2, None)
                if current is None:
                    break
                # print(i)
                if key2 == current[head]:
                    key2 = current[after]
                    value += current[content:]
                    continue
                else:
                    break
            if (len(value) >= LengthTag):
                value = WriteFileOnly(writer, value, absPath, typer)
                dic.pop(key1, None)
                dic.pop(key2, None)
                dic.pop(key, None)
                dic[key] = value
                dic[key1] = value
                dic[key2] = value
            # 设置时间戳
            value[after] = key2
            value[timeTag] = time.time()
            dic[key2] = value
            continue
        else:
            # 前增
            value = dic.pop(key2, None)
            if not value is None:
                # 在前增
                if key1 == value[after]:
                    # 重传数据包
                    # 略过
                    continue
                # 非重传数据包
                value.insert(content, pkt.data)
                # while True:
                #     current = 
                # 设置时间戳
                value[timeTag] = time.time()
                value[head] = key1
                dic[key1] = value
                continue
            else:
                value = dic.pop(key, None)
                if value is None:
                    try:
                        # 初始化加入报文
                        http = Response(pkt.data)
                        chunked_tag = False
                        if http.headers.get('transfer-encoding', '').lower() == 'chunked':
                            chunked_tag = True
                        if judgeDcm(http.body):
                            value = [key1, key2, src + '-' + str(pkt.sport), dst + '-' + str(pkt.dport), time.time()]
                            fileName = str(time.time()) + '_' + value[srcPort] + '_' + value[dstPort] + '.dcm'
                            value.append(fileName)
                            value.append(chunked_tag)
                            value.append(http.body)
                            dic[key] = value
                            dic[key1] = value
                            dic[key2] = value
                            pass
                        elif judgeAstm(http.body):
                            value = [key1, key2, src + '-' + str(pkt.sport), dst + '-' + str(pkt.dport), time.time()]
                            fileName = str(time.time()) + '_' + value[srcPort] + '_' + value[dstPort] + '.astm'
                            value.append(fileName)
                            value.append(chunked_tag)
                            value.append(http.body)
                            dic[key] = value
                            dic[key1] = value
                            dic[key2] = value
                        elif filter:
                            value = [key1, key2, src + '-' + str(pkt.sport), dst + '-' + str(pkt.dport), time.time()]
                            fileName = str(time.time()) + '_' + value[srcPort] + '_' + value[dstPort] + '.unknow'
                            value.append(fileName)
                            value.append(chunked_tag)
                            value.append(http.body)
                            dic[key] = value
                            dic[key1] = value
                            dic[key2] = value
                            pass
                    except NeedData as err:
                        print(err)
                        continue
                    except UnpackError:
                        pass
                    continue
                # 对于乱序数据包的处理
                fileName = value[fileTag]
                chunked_tag = value[chunked]
                dic[key] = value
                value = [key1, key2, src + '-' + str(pkt.sport), dst + '-' + str(pkt.dport), time.time(), fileName, chunked_tag, pkt.data]
                dic[key1] = value
                dic[key2] = value
                continue
    # 输出运行时间
    # print(time.time() - allTime, i)
    while t.isAlive():
        writer.quit()
        time.sleep(1)
    return os.path.join(absPath, typer)
    # for path in os.listdir(os.path.join(absPath, typer)):
    #     readByProtocol(os.path.join(absPath, typer, path), typer)

if __name__ == '__main__':
    # construct('E:\\29161\\Destop\\medical_instance\\pcap', 'test6.pcap', 'http')
    # construct('pcap', 'http_download.pcap', 'http', filter=True)
    import threading
    t1 = threading.Thread(target=construct, args=['pcap/1589985453/', 'http.pcap', 'DICOM|http', True])
    import dpktConstruct
    t2 = threading.Thread(target=dpktConstruct.construct, args=['pcap/1589985453/', 'http.pcap', 'DICOM|ftp'])
    t1.start()
    t2.start()
    