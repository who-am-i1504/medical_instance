from .state import State, Lexer, FileReader, Token, dealIPPort
from .constant import SB, EB, Escape, Component, Field, Subcomponent, Repeat, HL7Separator, TokenType
from .database.tables import *
import copy

class LexerHL7(Lexer):

    def __init__(self, datapath, fileOperator=None):
        if fileOperator is None:
            super(LexerHL7, self).__init__(FileReader(datapath), copy.deepcopy(HL7Separator))
        else:
            super(LexerHL7, self).__init__(FileReader(datapath, fileOperator), copy.deepcopy(HL7Separator))
    
    def set_separator(self):
        super().set_separator(copy.deepcopy(HL7Separator))

    def get_alpha(self):
        str_list = []
        if self.peek.isdigit() or self.peek.isalpha():
            while self.peek.isdigit() or self.peek.isalpha():
                str_list.append(self.peek)
                self.read_alpha()
            return Token(b''.join(str_list), TokenType['word'])
        else:
            str_list = self.peek
            self.read_alpha()
            if str_list == SB:
                return Token(str_list, TokenType['start'])
            else:
                return Token(str_list, TokenType['word'])

    def get_field(self):
        str_list = []
        if self.peek in self.separator:
            str_list = self.peek
            self.read_alpha()
            return Token(str_list, TokenType['delitimter'])
        elif self.peek == SB:
            return Token(SB, TokenType['syntx'])
        elif self.peek == EB:
            str_list = EB
            self.read_alpha()
            return Token(str_list, TokenType['end'])
        else:
            while not (self.peek in self.separator) and self.peek[0] != 0:
                if (self.peek[0] > 0 and self.peek[0] < 29) or (self.peek[0] > 30 and self.peek[0] < 32) or self.peek[0] >= 129:
                    return Token(b''.join(str_list), TokenType['syntx'])
                str_list.append(self.peek)
                self.read_alpha()
            if (len(str_list) == 0 and (self.peek[0] == 0 )):
                return Token(self.peek, TokenType['string'])
            return Token(b''.join(str_list), TokenType['string'])
        pass

class StateHL7(State):
    def __init__(self, data, fileOperator=None):
        if fileOperator is None:
            self.lexer = LexerHL7(data)
        else:
            self.lexer = LexerHL7(data, fileOperator)
        self.result = {
            'main': None,
            'segment': []
        }
        self.initData()
        src, sport, dst, dport = dealIPPort(data)
        super(StateHL7, self).__init__(
            self.lexer, self.result, src, sport, dst, dport)
        self.function = [self.lexer.set_field, self.lexer.set_component,
                    self.lexer.set_repeat, self.lexer.set_escape, self.lexer.set_subcomponent]
        pass
        
    def initData(self):
        self.result = {
            'main': None,
            'segment': []
        }
        self.segment = None
        self.seg_seq = 1
        self.seg_name = None
        self.batch = False
        self.seg_content = []
        self.field_num = 0
        self.field_end_place = 0
        self.lexer.set_separator()
        self.lexer.set_state(0)
    
    def getField(self):
        self.seg_content.append(self.peek.getToken())
        self.get_next()
        i = 0
        while not self.peek.getToken() in self.lexer.separator[0:2] and not self.peek.getToken() in [SB, EB, b'\x00']:
            self.seg_content.append(self.peek.getToken())
            self.get_next()
            i = i + 1
        string = ''
        if i != 0:
            string = ''.join(
                str(x, 'utf8') for x in self.seg_content[0 - i:])
        return string
    
    def getComponent(self):
        # 此处需要考虑重复分隔符对于该字段位置的影响，暂时未写(不知道具体的方式)
        
        if self.peek.getType() == TokenType['delitimter']:
            if self.peek.getToken() == self.lexer.separator[Field]:
                self.field_num = self.field_num + 1
                # 做出相关词处理
                if self.batch == False and self.seg_name == b'MSH':
                    if self.field_num == 9:
                        # 消息类型
                        self.result['main'].type = self.getField()
                    elif self.field_num == 12:
                        # 消息版本
                        self.result['main'].version = self.getField()
                    elif self.field_num == 13:
                        # 消息序列号
                        self.result['main'].seqnumber = self.getField()
                        if self.result['main'].seqnumber == '':
                            self.result['main'].seqnumber = None
                    else:
                        self.seg_content.append(self.peek.getToken())
                        self.get_next()
                    pass
                else:
                    self.seg_content.append(self.peek.getToken())
                    self.get_next()
                pass
            else:
                self.seg_content.append(self.peek.getToken())
                self.get_next()
            pass
        else:
            if self.field_num == 1:
                if self.peek.getToken() == b'DSC':
                    self.result['main'].dsc_status = True
                self.seg_name = self.peek.getToken()
                if not self.segment == None:
                    if self.peek.getToken() == b'ADD':
                        self.segment.add_status = True
                    self.seg_content = []
                # 此处是否添加验证(即对消息内部的消息段的排列顺序,包括段组的划分)
                self.segment = Segment()
                self.segment.name = self.peek.getToken()
                self.segment.seq = self.seg_seq
                self.seg_seq = self.seg_seq + 1
                self.segment.delimiter = b''.join(self.lexer.separator[1:])
                self.segment.add_status = False
            self.seg_content.append(self.peek.getToken())
            self.get_next()

    def getRecord(self):
        if not self.segment is None:
            self.segment.content = ''.join(
                str(x, 'utf8') for x in self.seg_content)
            self.result['segment'].append(self.segment)
            self.seg_seq = self.seg_seq + 1
        else:
            pass
        self.seg_content = []
        self.field_num = 1
        if self.peek.getType() == TokenType['delitimter']:
            self.get_next()
        elif self.peek.getType() == TokenType['end']:
            self.end_state()
            self.get_next()
            return
        else:
            self.get_next()
        pass

    def write(self):
        session = DBSession()
        self.result['main'].complete_status = True
        session.add(self.result['main'])
        session.flush()
        id = self.result['main'].id
        for data in self.result['segment']:
            data.id = id
            session.add(data)
        session.commit()
        session.close()

    def end_state(self):
        if self.lexer.peek == b'\x0d':
            # 结束处理
            self.get_next()
            if not self.segment == None:
                self.result['segment'].append(self.segment)
                self.result['main'].complete_status = True
                self.result['main'].size = self.lexer.get_current_place() - self.result['main'].size
                self.setMainIpPort(self.inIp, self.inPort,
                                   self.outIp, self.outPort)
                self.write()
                self.initData()
        else:
            self.lexer.set_state(0)
            self.get_next()
            return

    def getHeader(self):
        size = self.lexer.get_current_place()
        self.get_next()
        if self.peek.getToken() == b'MSH':
            self.result['main'] = MessageMain()
            self.result['main'].complete_status = False
        elif self.peek.getToken() == b'FHS':
            self.result['main'] = MessageMain()
            self.result['main'].type = 'BATCH'
            self.result['main'].complete_status = False
            self.batch = True
        elif self.peek.getToken() == b'BHS':
            self.result['main'] = MessageMain()
            self.result['main'].type = 'BATCH'
            self.result['main'].complete_status = False
            self.batch = True
        else:
            return
        self.result['main'].size = size
        self.seg_content.append(self.peek.getToken())
        self.seg_name = self.peek.getToken()
        self.segment = Segment()
        self.segment.name = self.peek.getToken()
        self.segment.seq = self.seg_seq
        self.seg_seq = self.seg_seq + 1
        self.segment.add_status = False
        self.getDelimiter()
        self.segment.delimiter = ''.join(
            str(i, 'utf8') for i in self.lexer.separator[1:])
        self.field_num = 2
    
    def getDelimiter(self):
        delitimter = []
        for i in range(Field, Subcomponent + 1):
            self.get_next()
            if self.peek.getToken().isdigit() or self.peek.getToken().isalpha() or self.peek.getToken()[0] < 29 or (self.peek.getToken()[0] > 30 and self.peek.getToken()[0] < 33) or (self.peek.getToken()[0] > 129):
                self.lexer.set_separator()
                return
            if (not self.peek.getToken() == self.lexer.separator[i]) and len(self.peek.getToken()) == 1:
                self.function[i - 1](self.peek.getToken())
            elif len(self.peek.getToken()) > 1:
                self.initData()
                return
            delitimter.append(self.peek.getToken())

        self.seg_content.append(b''.join(delitimter))
        self.lexer.set_state(1)
        if self.lexer.peek == self.lexer.separator[Field]:
            self.get_next()
            self.segment.delimiter = ''.join(
                str(x, 'utf8') for x in self.lexer.separator[1:])
            self.seg_content.append(self.peek.getToken())
        else:
            self.lexer.set_state(0)
            self.get_next()
            self.initData()
            return 


def testTotalFile():
    s = StateHL7('HL7Test/hl7_1589277228.7895925_205.167.25.101-21_10.246.229.255-52466')
    s.state()
    pass
def testPartFile():
    s = StateHL7('HL7Test/hl7part_1589277228.7895925_205.167.25.101-21_10.246.229.255-52466')
    s.state()
    pass
def testServalFiles():
    s = StateHL7('HL7Test/hl7serval_1589277228.7895925_205.167.25.101-21_10.246.229.255-52466')
    s.state()
    pass

if __name__ == '__main__':
    testTotalFile()
    testPartFile()
    testServalFiles()