from .constant import TokenType 
import os
import asyncio

class Token:
    # type 类型
    # 0 为读取的分隔符
    # 1 为单字符读取的数据
    # 2 为字符串读取取得的token
    # 3 为单字符读取读取的分隔符
    # 4 为其他情况
    def __init__(self, token, token_type):
        self.token = token
        self.token_type = token_type
    def getType(self):
        return self.token_type
    def getToken(self):
        return self.token

class State:
    
    def __init__(self, lexer, result, inIp, inPort, outIp, outPort):
        self.lexer = lexer
        self.inIp = inIp
        self.inPort = inPort
        self.outIp = outIp
        self.outPort = outPort
        self.peek = ''
        self.result = result
        pass

    def initData(self):
        print('Instance in SubClass!')

    def setMainIpPort(self, inIP, inPort, outIP, outPort):
        self.setMainInIpPort(inIP, inPort)
        self.setMainOutIpPort(outIP, outPort)
        pass

    def setMainInIpPort(self, inIP, inPort):
        self.result['main'].send_ip_port = inIP + ':' + inPort
        pass
    
    def setMainOutIpPort(self, outIP, outPort):
        self.result['main'].receiver_ip_port = outIP + ':' + outPort
        pass
    
    def get_next(self):
        self.peek = self.lexer.getToken()

    def state(self):

        self.get_next()

        while isinstance(self.peek, Token) and self.peek.getToken() != b'\x00':
            # self.peek = self.lexer.get_alpha()
            if self.peek.getType() == TokenType['syntx']:
                self.initData()
                self.get_next()
                continue
            if self.peek.getType() == TokenType['start']:
                self.getHeader()
            elif self.peek.getToken() == b'\x0d' or self.peek.getType() == TokenType['end']:
                self.getRecord()
            elif self.peek.getType() == TokenType['delitimter'] \
                or self.peek.getType() == TokenType['string'] \
                or self.peek.getType() == TokenType['escape']:
                self.getComponent()
                pass
            elif self.peek.getType() == TokenType['word']:
                self.get_next()
            else:
                print('error in this State!')
                break
            pass
        pass

    def getHeader(self):
        print('please finish its Son class!')
        pass

    def getRecord(self):
        print('please finish its Son class!')
        pass

    def getComponent(self):
        print('please finish its Son class!')
        pass

    def setIpPort(self, inIp, inPort, outIp, outPort):
        self.inIp = inIp
        self.inPort = inPort
        self.outIp = outIp
        self.outPort = outPort

def dealIPPort(path):
    (head, tail) = os.path.split(path)
    ip_port = tail.split('_')
    src_port = ip_port[2]
    dst_port = ip_port[3]
    src_port = src_port.split('-')
    src = src_port[0]
    sport = src_port[1]
    dst_port = dst_port.split('-')
    dst = dst_port[0]
    dport = dst_port[1]
    if '.' in dport:
        dport = dport[:dport.index('.')]
    return src, sport, dst, dport


class Lexer:

    def __init__(self, data, separator):
        # 需要解析的数据
        self.data = data
        # 保存的分隔符列表
        self.separator = separator
        # self.back = b''
        # 当前的字符
        self.peek = b''
        # 需要解析的数据的长度
        self.length = self.data.all_length
        # 所处状态
        self.state = 0
        # 解析的指针，即解析到的字符位置
        self.place = 0
        # 首先读取一个字符
        self.read_alpha()

    def get_current_place(self):
        return self.place

    # 对外暴露的获取单元接口
    def getToken(self):
        if self.state == 0:
            return self.get_alpha()
        elif self.state == 1 or self.state == 2:
            return self.get_field()

    def get_alpha(self):
        print('There is Nothing! Please construct this SonClass!')
        return b'\x00'

    def read_alpha(self):
        if self.place < self.length:
            self.peek = chr(self.data[self.place]).encode()
            self.place = self.place + 1
        else:
            self.peek = b'\x00'

    def get_field(self):
        print('There is Nothing! Please construct this SonClass!')
        return b'\x00'

    def set_separator(self, separator):
        self.separator = separator

    # 设置状态
    def set_state(self, state):
        self.state = state
    
    def get_state(self):
        return self.state

    # 设置字段分隔符
    def set_field(self, separator):
        self.separator[Field] = separator

    # 设置组件分隔符
    def set_component(self, separator):
        self.separator[Component] = separator

    # 设置重复分隔符
    def set_repeat(self, separator):
        self.separator[Repeat] = separator

    # 设置转义字符
    def set_escape(self, separator):
        self.separator[Escape] = separator

    # 设置子组件分隔符
    def set_subcomponent(self, separator):
        self.separator[Subcomponent] = separator


class FileReader:

    __fileSize__ = 1024*1024

    def __init__(self, filePath, fileObject=None):
        if fileObject == None and os.path.exists(filePath):
            self.file = open(filePath, 'rb')
        elif not fileObject is None:
            self.file = fileObject
        else:
            return None
        self.data = None
        # self.pre_data = None
        self.length = os.path.getsize(filePath)
        self.size = 0
        self.pre_length = 0
        self.file_end = False
        self.all_length = 0
        self.update()

    # 用于设置切片和索引的起始位置，并进行响应的值的转换和数据的处理
    def set_start(self, start):
        if start - self.pre_length == self.size:
            self.size = 0
            self.update()
            self.pre_length == 0
            return True
        elif start - self.pre_length < self.size and start >= self.pre_length:
            self.size = self.size - (start - self.pre_length)
            self.data = self.data[start - self.pre_length:]
            self.pre_length = 0
            return True
        else:
            return False

    # 用于文件的固定长度读取，
    def update(self):
        # self.pre_data = self.data
        self.data = self.file.read(self.__fileSize__)
        if self.size >= 0:
            self.pre_length = self.pre_length + self.size
        self.size = len(self.data)
        if self.size <= 0:
            self.file_end = True
        self.all_length = self.all_length + self.size

    # 用于返回从当前开始位置的到文件结束的长度，基于操作系统对于文件大小的读取与读取过文件内容的差值
    def __len__(self):
        return self.length - self.all_length + self.size

    # 本方法主要用于重写索引和切片，由于基于文件的固定长度读取，
    # 因此文件的读取只能一直向前，所以索引的访问只能一直向前，不能向后，
    # 同理，切片也是如此，这是本方法的一个弊端，还需要另外考虑对于图像文件的存储，
    # 保证图像文件占用的内存在可控范围内
    def __getitem__(self, item):
        if type(item) == int:
            while item - self.pre_length >= self.size and not self.file_end:
                self.update()
            if self.file_end:
                return None
            if item - self.pre_length >= 0:
                return self.data[item - self.pre_length]
            else:
                return None  # 不支持向已经丢失的内容查找
        elif type(item) == slice:
            start = item.start - self.pre_length
            stop = item.stop - self.pre_length
            if self.file_end:
                return None
            while start >= self.size and not self.file_end:
                self.update()
                start = start - self.size
                stop = start - self.size

            if self.file_end or start < 0 or stop <= 0:
                return None

            if start < self.size and stop <= self.size:
                return self.data[start:stop]
            elif start < self.size and stop > self.size:
                result = self.data[start:self.size]
                while stop > self.size and not self.file_end:
                    self.update()
                    result = result + self.data
                    stop = stop - self.size
                if self.file_end and self.size <= 0:
                    return result
                result = result + self.data[0: stop]
                return result
            else:
                return None
        else:
            return None

    def __del__(self):
        self.file.close()
