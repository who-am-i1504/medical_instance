import os
import sys
from dpkt.ip import IP
from dpkt.tcp import TCP
from dpkt.dpkt import NeedData
from dpkt.pcap import Reader as PReader
from dpkt.ethernet import Ethernet
from socket import inet_ntop
from socket import AF_INET
from socket import AF_INET6
from threading import Thread
from collections import defaultdict
import dpkt

from .nioWrite import NIOWriter
import time

# 一些提前定义的变量
LengthTag = 1000

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

# 是否为DICOM数据传输标志
DCMTAG = 6

# 一次PDU建立连接到结束的标志
Transfer = 7

keyReverse = 8
keyIndex = 9
# 内容开始位置
content = 10

# 用于超时的时间限制
# 即每隔多长时间检查一次字典中的无效数据
TimeThreshold = 1

# 对应标志值
PDU1 = 1 # 一次传输已经结束，即下一个包应该为建立连接
PDU2 = 2 # 传输正在进行
PDU3 = 3 # 不确定当前状态
PDU4 = 4
PDU5 = 5
PDU6 = 6
PDU7 = 7
NotEnsure = 8
END = 9
PDU567 = 10

PDU4Tag = b'\x04\x00'
PDU5Tag = b'\x05\x00'
PDU6Tag = b'\x06\x00'


def byte2number(number):
    sum = 0
    for x in number:
        sum = sum*256 + x
    return sum

def byte2number2(number):
    sum = 0
    i = 0
    for x in number:
        if i == 0:
            sum += x
        else:
            sum += x * (256**2)
        i+=1
    return sum

class PDUStream:
    def __init__(self, key, key1, key2, key3, src, dst, fileName, target, writer, absPath, typer):
        self.dic = {
            head:key1,
            after:key2,
            srcPort:src,
            dstPort:dst,
            timeTag:time.time(),
            fileTag:fileName,
            DCMTAG:True,
            Transfer:NotEnsure,
            keyReverse:key3,
            keyIndex:key,
            content:[]
        }
        self.absPath = absPath
        self.typer = typer
        self.target = target
        self.writer = writer
        self.FLength_02_00 = 0
        self.version_02_01 = None
        self.sopUID_02_02 = None
        self.sopInUID_02_03 = None
        self.trans_02_10 = None
        self.imp_02_12 = None
        self.result = []
    
    def getValue(self,item):
        return self.dic[item]
    
    def setValue(self, item, value):
        self.dic[item] = value
    
    def pdu1Deal(self, reader):
        PDULength = byte2number(reader[2:6])
        if PDULength <= 8:
            self.dic[DCMTAG] = False
            self.dic[content] = []
            return False
        pdu = reader[6:]
        juLeng = len(pdu)
        for i in self.dic[content]:
            if juLeng >= PDULength:
                break
            juLeng += len(i)
        if juLeng < PDULength:
            self.dic[content].insert(0, reader)
            return False
        while len(pdu) < PDULength:
            # if len(self.dic[content]) == 0:
            #     self.dic[DCMTAG] = False
            #     self.dic[content] = []
            #     return False
            pdu = b''.join([pdu, self.dic[content].pop(0)])
        if len(pdu) > PDULength:
            self.dic[DCMTAG] = False
            self.dic[content] = []
            return False
        self.dic[Transfer] = PDU1
        self.version_02_01 = pdu[0:2]
        self.FLength_02_00 = 0
        return PDU1
    
    def pdu2Deal(self, reader):
        
        self.FLength_02_00 = 0
        PDULength = byte2number(reader[2:6])
        if PDULength <= 8:
            self.dic[DCMTAG] = False
            self.dic[content] = []
            return False
        pdu = reader[6:]
        juLeng = len(pdu)
        for i in self.dic[content]:
            if juLeng >= PDULength:
                break
            juLeng += len(i)
        if juLeng < PDULength:
            self.dic[content].insert(0, reader)
            return False
        while len(pdu) < PDULength:
            # if len(self.dic[content]) == 0:
            #     self.dic[DCMTAG] = False
            #     self.dic[content] = []
            #     return False
            pdu = b''.join([pdu, self.dic[content].pop(0)])
        if len(pdu) > PDULength:
            self.dic[DCMTAG] = False
            self.dic[content] = []
            return False
        self.dic[Transfer] = PDU2
        start = 6 + 64
        t_tag = 0
        i_tag = 0
        try:
            i = start
            while i < PDULength:
                if (t_tag + i_tag) >= 2:
                    break
                if pdu[i:i + 2] == b'\x40\x00' and t_tag < 1:
                    leng = byte2number(pdu[i + 2 : i + 4])
                    self.trans_02_10 = pdu[i + 4: i + 4 + leng]
                    i = leng + i + 4
                    t_tag += 1
                    continue
                elif pdu[i:i + 2] == b'\x52\x00' and i_tag < 1:
                    leng = byte2number(pdu[i + 2:i + 4])
                    self.imp_02_12 = pdu[i + 4: i + 4 + leng]
                    i_tag += 1
                    i = leng + i + 4
                    continue
                else:
                    i += 1
        except:
            self.dic[DCMTAG] = False
            self.dic[content] = []
            return False
        self.dic[Transfer] = PDU2
        self.version_02_01 = pdu[0:2]
        return PDU2
    
    def pdu4Deal(self, reader):
        PDULength = byte2number(reader[2:6])
        pdv = b''.join([reader[6:]])
        juLeng = len(pdv)
        for i in self.dic[content]:
            if juLeng >= PDULength:
                break
            juLeng += len(i)
        if juLeng < PDULength:
            self.dic[content].insert(0, reader)
            return False
        while len(pdv) < PDULength:
            # if len(self.dic[content]) == 0:
            #     self.dic[DCMTAG] = False
            #     self.dic[content] = []
            #     return False
            mid_data = self.dic[content].pop(0)
            last_dis = PDULength - len(pdv)
            if last_dis < len(mid_data):
                pdv = b''.join([pdv, mid_data[0:last_dis]])
                self.dic[content].insert(0, b''.join([mid_data[last_dis:]]))
            else:
                pdv = b''.join([pdv, mid_data])
        if len(pdv) > PDULength or PDULength < 20:
            self.dic[DCMTAG] = False
            self.dic[content] = []
            return False
        if not byte2number(pdv[0:4]) == PDULength - 4:
            self.dic[DCMTAG] = False
            self.dic[content] = []
            return False
        try:
            p_context = pdv[4]
            self.dic[Transfer] = PDU4
            if pdv[5] == 3:
                start = 6
                t_tag = 0
                i_tag = 0
                i = start
                while i < PDULength:
                    if i >= PDULength - 4 or (t_tag + i_tag) >= 2:
                        break
                    if pdv[i:i + 4] == b'\x00\x00\x02\x00' and t_tag < 1:
                        leng = pdv[i + 4 : i + 8]
                        # self.result.append(leng)
                        leng = byte2number2(leng)
                        self.sopUID_02_02 = pdv[i+8:i + 8 + leng]
                        t_tag += 1
                        i = i+8 + leng
                        continue
                    elif pdv[i : i + 4] == b'\x00\x00\x00\x10' and i_tag < 1:
                        leng = pdv[i + 4:i + 8]
                        # self.result.append(leng)
                        leng = byte2number2(leng)
                        self.sopInUID_02_03 = pdv[i + 8 : i + 8 + leng]
                        i_tag += 1
                        i = i+8 + leng
                        continue
                    else:
                        leng = pdv[i + 4:i+8]
                        leng = byte2number2(leng)
                        i = i + 8 + leng
            elif pdv[5] == 0 or pdv[5] == 2:
                d = pdv[6:]
                self.FLength_02_00 += len(d)
                self.result.append(d)
                if pdv[5] == 2:
                    o = None
                    if self.dic[keyReverse] in self.target.keys():
                        o = self.target[self.dic[keyReverse]]
                    self.setParams(o)
                    self.dic[Transfer] == END
                    self.writeFile()
        except Exception as e:
            # print(e)
            self.dic[DCMTAG] = False
            self.dic[content] = []
            return False
        return PDU4

    def generate(self):
        reader = self.dic[content].pop(0)
        while len(reader) < 6:
            if len(self.dic[content]) == 0:
                return False
            reader = b''.join([reader, self.dic[content].pop(0)])
        if self.dic[Transfer] == NotEnsure or self.dic[Transfer] == END:
            # 判断是否为PDU 类型1
            if reader[0:2] == b'\x01\x00':
                return self.pdu1Deal(reader)
            elif reader[0:2] == b'\x02\x00':
                return self.pdu2Deal(reader)
            elif reader[0:2] == b'\x03\x00':
                return PDU3
            elif reader[0:2] == b'\x04\x00':
                return PDU4
            elif reader[0:2] == b'\x05\x00':
                return PDU5
            elif reader[0:2] == b'\x06\x00':
                return PDU6
            elif reader[0:2] == b'\x07\x00':
                return PDU7
            else:
                self.dic[content] = []
                self.dic[DCMTAG] = False
                return False
        else:
            if reader[0:2] == b'\x04\x00':
                return self.pdu4Deal(reader)
            elif reader[0:2] == b'\x05\x00' or reader[0:2] == b'\x06\x00' or reader[0:2] == b'\x07\x00':
                PDULength = byte2number(reader[2:6])
                pdv = reader[6:]
                juLeng = len(pdv)
                for i in self.dic[content]:
                    if juLeng >= PDULength:
                        break
                    juLeng += len(i)
                if juLeng < PDULength:
                    self.dic[content].insert(0, reader)
                    return False
                while len(pdv) < PDULength:
                    # if len(self.dic[content]) == 0:
                    #     self.dic[DCMTAG] = False
                    #     self.dic[content] = []
                    #     return False
                    pdv = b''.join([pdv, self.dic[content].pop(0)])
                return PDU567
            else:
                return False     

    def push(self, value):
        if not self.dic[DCMTAG]:
            return 
        if len(value) > 0:
            self.dic[content].append(value)
        if len(self.dic[content]) >= 1000:
            self.generate()
    
    def writeFile(self):
        length = len(self.imp_02_12)
        if length & 1 == 1:
            self.imp_02_12 = b''.join([self.imp_02_12, b'\x00'])
            length += 1
        imp = b''.join([b'\x02\x00\x12\x00', b'\x55\x49', length.to_bytes(length=2,byteorder='little',signed=False), self.imp_02_12])
        self.FLength_02_00 += len(imp)
        self.result.insert(0, imp)
        length = len(self.trans_02_10)
        if length & 1 == 1:
            self.trans_02_10 = b''.join([self.trans_02_10, b'\x00'])
            length += 1
        trans = b''.join([b'\x02\x00\x10\x00', b'\x55\x49', length.to_bytes(length=2,byteorder='little',signed=False), self.trans_02_10])
        self.FLength_02_00 += len(trans)
        self.result.insert(0, trans)
        length = len(self.sopInUID_02_03)
        if length & 1 == 1:
            self.trans_02_10 = b''.join([self.trans_02_10, b'\x00'])
            length += 1
        sopInUID = b''.join([b'\x02\x00\x03\x00', b'\x55\x49', length.to_bytes(length=2,byteorder='little',signed=False), self.sopInUID_02_03])
        self.FLength_02_00 += len(sopInUID)
        self.result.insert(0, sopInUID)
        length = len(self.sopUID_02_02)
        if length & 1 == 1:
            self.sopUID_02_02 = b''.join([self.sopUID_02_02, b'\x00'])
            length += 1
        sopUID = b''.join([b'\x02\x00\x02\x00', b'\x55\x49', length.to_bytes(length=2,byteorder='little',signed=False), self.sopUID_02_02])
        self.FLength_02_00 += len(sopUID)
        self.result.insert(0, sopUID)
        length = len(self.version_02_01)
        if length & 1 == 1:
            self.version_02_01 = b''.join([self.version_02_01, b'\x00'])
            length += 1
        version = b''.join([b'\x02\x00\x01\x00', b'\x4F\x42\x00\x00', length.to_bytes(length=2,byteorder='little',signed=False), b'\x00\x00' , self.version_02_01])
        self.FLength_02_00 += len(version)
        self.result.insert(0, version)
        if self.FLength_02_00 & 1 == 1:
            self.result.append(b'\x00')
            self.FLength_02_00 += 1
        fileLength = self.FLength_02_00.to_bytes(length=4,byteorder='little',signed=False)
        length = len(fileLength)
        fLength = b''.join([b'\x02\x00\x00\x00\x55\x4C', length.to_bytes(length=2,byteorder='little',signed=False), fileLength])
        self.result.insert(0, fLength)
        self.result.insert(0, b'\x44\x49\x43\x4D')
        header = b'\x00' * 128
        self.result.insert(0, header)
        item ={}
        item = {}
        item['fileName'] = 'Y_%s_%s_%s' % (self.dic[timeTag], self.dic[srcPort], self.dic[dstPort])
        item['absPath'] = os.path.join(self.absPath, self.typer)  
        item['data']=self.result
        self.writer.put(item)
        self.result = []
        self.dic[timeTag] = time.time()
        self.FLength_02_00 = 0
        self.version_02_01 = None
        self.sopUID_02_02 = None
        self.sopInUID_02_03 = None
        self.trans_02_10 = None
        self.imp_02_12 = None

    def FinDeal(self):
        if self.dic[DCMTAG]:
            while len(self.dic[content]) > 0:
                if self.generate() is False:
                    break
        self.target.pop(self.dic[head], None)
        self.target.pop(self.dic[after], None)
        self.target.pop(self.dic[keyIndex], None)
        another = self.target.pop(self.dic[keyReverse], None)
        if another is not None:
            another.FinDeal()
    
    def RSTDeal(self):
        if self.dic[DCMTAG] is False:
            return
        while(len(self.dic[content]))>0:
            if self.generate() is False:
                break
        
    def getState(self):
        return self.dic[Transfer]

    def setParams(self, o):
        # o.generate()
        if o is None or (o.trans_02_10 is None and o.imp_02_12 is None):
            self.trans_02_10 = b'1.2.840.10008.1.2.1'
            self.imp_02_12 = b'1.2.276.0.7230010.3.0.3.5.4'
        else:
            self.trans_02_10 = o.trans_02_10
            self.imp_02_12 = o.imp_02_12

    def insert(self, value):
        if len(value) > 0:
            self.dic[content].insert(0, value)
        if len(self.dic[content]) > 1000:
            self.generate()

    def pushPDUStream(self, stream):
        self.target.pop(stream.dic[head], None)
        self.target.pop(stream.dic[after], None)
        self.dic[content] += stream.dic[content]
        self.dic[after] = stream.dic[after]
        self.target.pop(self.dic[keyIndex], None)
        if len(self.dic[content]) >= 1000:
            self.generate()
        # self.target[self.dic[keyIndex]] = self

    def judge(self):
        if len(self.dic[content]) == 0:
            return False
        reader = self.dic[content][0]
        i = 1
        while len(reader) < 6 and i < len(self.dic[content]):
            reader = b''.join([reader, self.dic[content][i]])
            i += 1
        
        if len(reader) < 6:
            return False
        
        length = byte2number(reader[2:6])
        leng = len(reader) - 6
        while leng < length and i < len(self.dic[content]):
            leng += len(self.dic[content][i])
            i += 1
        if leng < length:
            return False
        return True


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

def construct(absPath, target, typer):
    if not os.path.exists(os.path.join(absPath, typer)):
        os.mkdir(os.path.join(absPath, typer))
    # fpcap = open(os.path.join(absPath, target), 'rb')
    writer = NIOWriter()
    t = Thread(target=writer.start_loop)
    t.start()
    time.sleep(1)
    dic = defaultdict(None)
    i = 0
    f = open(os.path.join(absPath, target), 'rb')
    pcap_reader = PReader(f)
    start = time.time()
    for timestamp, pkt in pcap_reader:
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
        i += 1
        # print(i, pkt.sport, pkt.dport)
        # if i <= 81:
        #     continue
        # 对pkt进行相应的处理
        now = time.time()
        if now - start >= TimeThreshold:
            for key in list(dic.keys()):
                if not key in dic:
                    continue
                value = dic[key]
                if (now - value[timeTag]) >= TimeThreshold:
                    dic.pop(value[head], None)
                    dic.pop(value[after], None)
            start = time.time()
       
        seq = pkt.seq + len(pkt.data)

        if (pkt.flags & 2) == 2:
            seq += 1
        key = src + ':' + str(pkt.sport) + '-' + dst + ':' + str(pkt.dport)
        key1 = src + ':' + str(pkt.sport) + '-' + dst + ':' + str(pkt.dport) + '_' + str(pkt.seq)
        key2 = src + ':' + str(pkt.sport) + '-' + dst + ':' + str(pkt.dport) + '_' + str(seq)
        key3 = dst + ':' + str(pkt.dport) + '-'  + src + ':' + str(pkt.sport)
        value = dic.pop(key1, None)
        
        if not value is None:
            # 追加
            if key1 == value.getValue(head) and value.getValue(head) != value.getValue(after):
                # 重传数据包
                # 略过
                continue
            # 非重传数据包
            value.push(pkt.data)
            if pkt.data[0:2] == PDU6Tag or pkt.data[0:2] == PDU4Tag:
                if value.judge():
                    value.generate()
            if (pkt.flags & 1) > 0 or (pkt.flags & 20) == 20:
                # 清除键值
                value.FinDeal()
                # if not dic.pop(key1, None) is None:
                #     print('here')
                continue
            # if (pkt.flags & 4) == 4:
            #     value.RSTDeal()
            #     continue
            if not value.getState():
                continue
            # 乱序数据包
            while True:
                current = dic.pop(key2, None)
                if current is None:
                    break
                # print(i)
                if key2 == current.getValue(head):
                    key2 = current.getValue(after)
                    value.pushPDUStream(current)
                    continue
                else:
                    break
            # 设置时间戳
            value.dic[after] = key2
            value.dic[timeTag] = time.time()
            dic[key2] = value
            dic[key] = value
            continue
        else:
            # 前增
            value = dic.pop(key2, None)
            if not value is None:
                # 在前增
                if key1 == value.getValue(after):
                    # 重传数据包
                    # 略过
                    continue
                # 非重传数据包
                value.insert(pkt.data)
                # 设置时间戳
                value.dic[timeTag] = time.time()
                value.dic[head] = key1
                dic[key1] = value
                continue
            else:
                value = PDUStream(key, key1, key2, key3, src + '-' + str(pkt.sport), dst + '-' + str(pkt.dport), '', dic, writer,absPath, typer)
                value.push(pkt.data)
                dic[key] = value
                dic[key1] = value
                dic[key2] = value
                continue

    # print(time.time() - allTime)
    while t.isAlive():
        writer.quit()
        time.sleep(1)
    return os.path.join(absPath, typer)
    # for path in os.listdir(os.path.join(absPath, typer)):
    #     readByProtocol(os.path.join(absPath, typer, path), typer)



# if __name__ == '__main__':
    # construct('E:\\29161\\Destop\\medical_instance\\pcap', 'test.pcap', 'http')
    # construct('pcap', 'dicomData.pcap', 'DICOM')
    # construct('pcap/1590832701', 'dicom.pcap', '../DICOM1')
    # construct('pcap/1589974224/', 'ftp.pcap', 'DICOM|ftp')
    # construct('E:\\29161\\Destop\\medical_instance\\pcap', 'http_download.pcap', 'http')
    # construct('E:\\29161\\Destop\\medical_instance\\pcap', 'http_download.pcap', 'http')
    # import threading
    # import dpktHttpConstruct
    # t1 = threading.Thread(target=dpktHttpConstruct.construct, args=['pcap/1589985453/', 'http.pcap', 'DICOM|http', True])
    # import dpktConstruct
    # t2 = threading.Thread(target=construct, args=['pcap/1589985453/', 'ftp.pcap', 'DICOM|ftp'])
    # t1.start()
    # t2.start()