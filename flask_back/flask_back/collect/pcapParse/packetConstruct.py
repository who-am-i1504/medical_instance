from scapy.all import *
from threading import Thread
from nioWrite import NIOWriter 
import time

head = 0
after = 1
srcPort = 2
dstPort = 3
timeTag = 4
content = 5

def FINDeal(dic, value, pkt, key1, key2, writer, absPath, typer):
    key3 = pkt['IP'].dst + ':' + str(pkt['TCP'].dport) + '-'  + pkt['IP'].src + ':' + str(pkt['TCP'].sport) +  '_' + str(pkt['IP'].ack)
    Another = dic.pop(key3, None)
    if not Another is None:
        if key3 == Another[head]:
            dic.pop(Another[after], None)
        else:
            dic.pop(Another[head], None)
        item = {}
        item['fileName'] = 'Y_%s_%s-%s_%s-%s' % (str(time.time()), str(pkt['IP'].dst), str(pkt['TCP'].dport), str(pkt['IP'].src),str(pkt['TCP'].sport))
        item['absPath'] = os.path.join(absPath, typer)
        item['data']=Another[content:]
        writer.put(item)
    item1 = {}
    item1['fileName'] = 'Y_%s_%s-%s_%s-%s' % (str(time.time()), str(pkt['IP'].src),str(pkt['TCP'].sport), str(pkt['IP'].dst), str(pkt['TCP'].dport))
    item1['absPath'] = os.path.join(absPath, typer)  
    item1['data']=value[content:]
    writer.put(item1)

def construct(absPath, target, typer):
    if not os.path.exists(os.path.join(absPath, typer)):
        os.mkdir(os.path.join(absPath, typer))
    # fpcap = open(os.path.join(absPath, target), 'rb')
    writer = NIOWriter()
    t = Thread(target=writer.start_loop)
    t.start()
    dic = defaultdict(None)
    i = 0
    start = time.time()
    with PcapReader(os.path.join(absPath, target)) as pcap_reader:#返回一个迭代器
        start = time.time()
        i = 0

        # for pkt in pcap_reader:
            # pass
        
        for pkt in pcap_reader:#for循环进行遍历
            i += 1
            #对pkt进行相应的处理
            # now = time.time()
            # if now - start > 1:
            #     for key in list(dic.keys()):
            #         if not key in dic:
            #             continue
            #         value = dic[key]
            #         if (now - value[timeTag]) >= 2:
            #             dic.pop(value[head], None)
            #             dic.pop(value[after], None)
            #             item = {}
            #             item['fileName'] = 'N_%s_%s_%s' % (str(time.time()), value[srcPort], value[dstPort])
            #             item['absPath'] = os.path.join(absPath, typer)
            #             item['data']=value[content:]
            #             writer.put(item)
            #     start = time.time()
            # i = 0
            if 'TCP' in pkt and 'IP' in pkt:
                # i += 1
                # print(i, repr(pkt))
                seq = pkt['TCP'].seq + len(pkt['TCP'].payload)
                # print(pkt['TCP'].flags)
                if (pkt['TCP'].flags & 2) == 2:
                    seq += 1
                key1 = pkt['IP'].src + ':' + str(pkt['TCP'].sport) + '-' + pkt['IP'].dst + ':' + str(pkt['TCP'].dport) + '_' + str(pkt['TCP'].seq)
                key2 = pkt['IP'].src + ':' + str(pkt['TCP'].sport) + '-' + pkt['IP'].dst + ':' + str(pkt['TCP'].dport) + '_' + str(seq)

                value = dic.pop(key1, None)
                
                if not value is None:
                    # 追加
                    if key1 == value[head]:
                        # 重传数据包
                        # 略过
                        continue
                    # 非重传数据包
                    
                    value.append(pkt['TCP'].payload)
                    # if i == 121:
                    #     print(pkt, pkt['TCP'].flags, pkt['TCP'].flags & 1)
                    if (pkt['TCP'].flags & 1) == 1:
                        # 清除键值
                        dic.pop(value[head], None)
                        dic.pop(value[after], None)
                        FINDeal(dic, value, pkt, key1, key2, writer, absPath, typer)
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
                            value.append(current[content:])
                            continue
                        else:
                            break
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
                        value.insert(content, pkt['TCP'].payload)

                        # while True:
                        #     current = 
                        # 设置时间戳
                        value[timeTag] = time.time()
                        value[head] = key1
                        dic[key1] = value
                        continue
                    else:
                        value = [key1, key2,pkt['IP'].src + '-' + str(pkt['TCP'].sport), pkt['IP'].dst + '-' + str(pkt['TCP'].dport), time.time() ,pkt['TCP'].payload]
                        dic[key1] = value
                        dic[key2] = value
                        continue
                        
    for key in list(dic.keys()):
        value = dic.pop(key, None)
        if value is None:
            continue
        item = {}
        item['fileName'] = 'N_%s_%s_%s' % (str(time.time()), value[srcPort], value[dstPort])
        item['absPath'] = os.path.join(absPath, typer)
        item['data']=value[content:]
        writer.put(item)
        dic.pop(value[head],None)
        dic.pop(value[after],None)
    print(time.time() - start)
