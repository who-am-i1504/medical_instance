from database.tables import *
from constant import Escape, Component, Field, Repeat, HChar2Value, AstmSeparator, TokenType, AstmDelimiterOrder
import os
from state import State, Token, Lexer, FileReader
import copy

class LexerAstm(Lexer):
    def __init__(self, dataPath):
        super(LexerAstm, self).__init__(FileReader(dataPath), copy.deepcopy(AstmSeparator))
    
    def set_separator(self):
        super().set_separator(copy.deepcopy(AstmSeparator))
    
    def get_alpha(self):
        current = self.peek
        self.read_alpha()
        if current == b'H':
            return Token(current, TokenType['start'])
        
        return Token(current, TokenType['word'])

    def get_field(self):
        str_list = []
        if self.peek in self.separator or self.peek == b'\x00':
            str_list = self.peek
            self.read_alpha()
            return Token(str_list, TokenType['delitimter'])
        # elif self.peek == EB:
        #     str_list = EB
        #     self.read_alpha()
        #     return str_list
        else:
            while not self.peek in self.separator :
                str_list.append(self.peek)
                self.read_alpha()
            return Token(b''.join(str_list), TokenType['string'])
        pass

class StateAstm(State):

    def __init__(self, file):
        lexer = LexerAstm(file)
        result = {
            'main': AstmMain(),
            'records': [],
            'status': False,
            'record_num': 0
        }
        super(StateAstm, self).__init__(
            lexer, result, '127.0.0.1', '8080', '127.0.0.1', '8081')
        self.cRecord = None
        self.peek = None
        self.cRecordHeader = ' '
        self.field_num = 0
        # self.component_num = 0
        self.record = []
        self.deli_functions = [self.lexer.set_field,
                               self.lexer.set_repeat, self.lexer.set_component, self.lexer.set_escape]
        
    def getHeader(self):
        self.result['record_num'] = 0
        self.lexer.set_separator()

        delimiter = []
        for i in range(len(AstmDelimiterOrder)):
            self.get_next()
            if self.peek.getToken().isdigit() or self.peek.getToken().isalpha() or self.peek.getToken()[0] < 29 or (self.peek.getToken()[0] > 30 and self.peek.getToken()[0] < 33) or (self.peek.getToken()[0] > 129):
                self.lexer.set_separator()
                return
            if self.lexer.separator[AstmDelimiterOrder[i]] != self.peek.getToken():
                self.deli_function(self.peek.getToken())
            delimiter.append(self.peek.getToken())
            pass
        self.lexer.set_state(1)
        if self.lexer.peek == delimiter[0] or self.lexer.peek == self.lexer.separator[0]:
            self.get_next()
            self.result['status'] = True
            self.result['main'].delimiter = b''.join(delimiter)
            self.cRecordHeader = 'H'
            self.field_num = 2
            # if self.peek == delimiter[0]:
            #     self.field_num = self.field_num + 1
            self.result['record_num'] = 1
            self.record.append(b'H')
            self.record.append(b''.join(delimiter))
            self.cRecord = AstmRecord()
            self.cRecord.patient_id = 0
            self.cRecord.order_id = 0
            self.cRecord.type = 'H'
            self.cRecord.delimiter = self.result['main'].delimiter
            self.cRecord.id = self.result['record_num']
            self.setMainIpPort(self.inIp, self.inPort,
                               self.outIp, self.outPort)
            pass
        else:
            self.lexer.set_state(0)
            self.get_next()

    def getComponent(self):
        if self.peek.getToken() == self.lexer.separator[Repeat]:
            # self.component_num = 0
            self.get_next()
            self.record.append(self.peek.getToken())
            pass
        elif self.peek.getToken() == self.lexer.separator[Field]:
            if self.cRecordHeader == 'H':
                self.HContent()
            else:
                self.record.append(self.peek.getToken())
                self.get_next()
            # if self.
            self.field_num = self.field_num + 1
            # self.component_num = 0
            #针对不同的记录类型判断其不同域的数据
        elif self.peek.getToken() not in self.lexer.separator:
            if self.field_num == 1:
                self.result['record_num'] = self.result['record_num'] + 1
                self.cRecordHeader = self.peek.getToken()
                lastRecord = self.cRecord
                self.cRecord = AstmRecord()
                self.cRecord.id = self.result['record_num']
                self.cRecord.type = self.cRecordHeader
                self.cRecord.delimiter = self.result['main'].delimiter
                if self.cRecordHeader == b'P':
                    if not (lastRecord is None):
                        self.cRecord.patient_id = lastRecord.patient_id + 1
                        self.cRecord.order_id = 0
                        lastRecord.p_continue = True
                        lastRecord.o_continue = False
                        # self.
                        pass
                    else:
                        pass
                    pass
                else:
                    self.cRecord.patient_id = lastRecord.patient_id
                    lastRecord.p_continue = False
                if self.cRecordHeader == b'O':
                    if not lastRecord is None:
                        self.cRecord.order_id = lastRecord.order_id + 1
                        lastRecord.o_continue = True
                        pass
                    pass
                elif self.cRecordHeader != b'P':
                    self.cRecord.order_id = lastRecord.order_id
                    lastRecord.o_continue = False
                if self.cRecordHeader == b'A':
                    if not lastRecord is None:
                        lastRecord._continue = True
                        pass
                    pass
                else:
                    lastRecord._continue = False
                self.cRecord.id = self.result['record_num']

            self.record.append(self.peek.getToken())
            self.get_next()
        else:
            self.get_next()

    def HContent(self):
        # if self.field_num == 6 or self.field_num == :
        if self.field_num >= 3 and self.field_num <= 14:
            self.record.append(self.peek.getToken())
            self.get_next()
            i = 0
            while not (self.peek.getToken() in self.lexer.separator[0:2]) and not (self.peek.getToken() in [b'\x00']):
                 self.record.append(self.peek.getToken())
                 self.get_next()
                 i = i + 1
            string = ''
            if i != 0:
                string = ''.join(
                        str(x, 'utf8') for x in self.record[0-i:])
            # self.record.append(self.peek.getToken())
            if self.field_num == 3:
                self.result['main'].message_id = string
            elif self.field_num == 4:
                self.result['main'].password = string
            elif self.field_num == 5:
                self.result['main'].sender = string
            elif self.field_num == 6:
                self.result['main'].sender_address = string
            elif self.field_num == 8:
                self.result['main'].sender_phone = string
            elif self.field_num == 9:
                self.result['main'].sender_character = string
            elif self.field_num == 10:
                self.result['main'].receiver_id = string
            elif self.field_num == 11:
                self.result['main'].receiver_type_id = string
            elif self.field_num == 12:
                self.result['main'].processing_id = string
            elif self.field_num == 13:
                self.result['main'].version = string
            elif self.field_num == 14:
                self.result['main'].message_time = string
            else:
                self.record.append(self.peek.getToken())

    def getRecord(self):
        self.result['records'].append(self.cRecord)
        self.cRecord.content = b''.join(self.record)
        if self.cRecordHeader == b'L':
            self.write()
            self.result['main'] = AstmMain()
            self.result['records'] = []
            self.result['status'] = 0
            self.result['record_num'] = 0
            self.lexer.set_state(0)
            self.lexer.set_separator()
            pass
        self.record = []
        self.field_num = 1
        self.cRecordHeader = ' '
        self.get_next()
        pass

    def write(self):
        session = DBSession()
        session.add(self.result['main'])
        session.flush()
        for item in self.result['records']:
            item.main_id = self.result['main'].id
            session.add(item)
            pass
        session.commit()
        print('success!')
