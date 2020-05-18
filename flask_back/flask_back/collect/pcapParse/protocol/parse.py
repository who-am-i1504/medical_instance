from database.tables import *
import os


class Parse:

    def __init__(self, filePath):
        self.data = FileReader(filePath)
        if self.data == None:
            return None
        self.type = 0
        self.result = None
        self.subitem = []
        self.size = len(self.data)
        self.write_database = True

    def judge_brunch(self):
        startByte = 0
        while self.data.set_start(startByte):
            self.size = len(self.data)
            self.subitem = []
            self.type = 0
            self.write_database = True
            type = self.data[0]
            if type == 1:
                startByte = self.brunch1()
            elif type == 2:
                startByte = self.brunch2()
            elif type == 3:
                startByte = self.brunch3()
            elif type == 4:
                startByte = self.brunch4()
            elif type == 5:
                startByte = self.brunch5()
            elif type == 6:
                startByte = self.brunch6()
            elif type == 7:
                startByte = self.brunch7()
            else:
                self.error_control('judge_brunch type')
                break
    
            if self.write_database:
                self.write()
                pass

    def write(self):
        session = DBSession()
        session.add(self.result)
        session.flush()
        session.commit()
        for i in self.subitem:
            i.pdu_id = self.result.id
            session.add(i)
            session.commit()
        session.close()

    def get_pdu_length(self):
        if self.size >= 6:
            self.size = self.byte2number(self.data[2:6])
            self.result.pdu_length = self.size
            self.size = self.size + 6
            return 6
        else:
            self.error_control('get_pdu_length')
            return 6
        pass

    def get_version(self):
        if self.size >= 8:
            self.result.protocol_version = self.byte2number(self.data[6:8])
            return 8
        else:
            self.error_control('get_version')
            return self.size
        pass

    def get_target_name(self):
        if self.size >= 26:
            self.result.called_ae_title = ''.join(chr(x) for x in self.data[10:26])
            return 26
        else:
            self.error_control('get_target_name')
            return self.size
        pass

    def get_source_name(self):
        if self.size >= 42:
            self.result.calling_ae_title = ''.join(
                chr(x) for x in self.data[26:42])
            return 42
        else:
            self.error_control('get_source_name')
            return self.size
        pass

    def judge75(self):
        if self.size >= 75 and int(self.data[74]) == 16:
            return 75
            pass
        else:
            self.error_control('function judge75')
            return self.size
    
    def error_control(self, message):
        self.write_database = False
        print('error in ', message, ' class Parse\n', end='')
    
    def mini_general(self, begin, data, size):
        if begin + 4 <= size:
            length = self.byte2number(data[begin + 2:begin + 4])
            if begin + length + 4 <= size:
                return length, data[begin + 4:begin + length + 4], begin + length + 4
            else:
                self.error_control('general in begin + length + 4')
                return None, None, size
        else:
            self.error_control('general in begin + 4')
            return None, None, size

    def general(self, begin):
        return self.mini_general(begin, self.data, self.size)
    
    def get_a_context(self):
        if not self.write_database:
            return self.size
        length, content, begin = self.general(74)
        if length == None:
            return begin
        else:
            self.result.a_context_length = length
            self.result.a_context_name = ''.join(chr(x) for x in content)
            return begin
    
    def get_p_context(self, begin):
        if not self.write_database:
            return self.size
        length, content, startByte = self.general(begin)
        if length == None:
            return startByte
        else:
            p = PContext()
            p.pdu_type = self.type
            p.p_context_length = length
            p.p_context_id = content[0]
            
            if 4 <= length:
                as_length = self.get_as(4, p, content)
                self.subitem.append(p)
                start = as_length + 8
                # 此处number为ts ID 如果采用自增序列，则应将此处代码屏蔽
                number = 1
                while start < length and content[start] == 64:
                    start = self.get_ts(start, p, content)
                    number = number + 1
                return startByte
            else:
                self.error_control('get_p_context 4 <= length')
                return startByte
            
    def get_as(self, begin, current, content):
        if not self.write_database:
            return self.size
        if content[begin] == 48:
            length, as_content, startByte = self.mini_general(begin, content, current.p_context_length)
            if length == None:
                return startByte
            else:
                current.as_length = length
                current.as_name = ''.join(chr(x) for x in as_content)
                return current.as_length
        else:
            self.error_control('get_as startByte != 48')
            return begin

    def get_ts(self, begin, p, content):
        if not self.write_database:
            return self.size
        length, ts_content, begin = self.mini_general(begin, content, p.p_context_length)
        if length == None:
            return begin
        else:
            current = TransferSyntaxSubitem()
            current.pdu_type = self.type
            current.p_context_id = p.p_context_id
            current.ts_length = length
            current.ts_name = ''.join(chr(x) for x in ts_content)
            self.subitem.append(current)
            return begin

    def get_user_info(self, begin):
        if not self.write_database:
            return self.size
        if begin < self.size and self.data[begin] == 80:
            length, content, startByte = self.general(begin)
            if length == None:
                return startByte
            self.result.user_info_length = length
            start = 0
            number = 80
            while content[0] == 81 and start < length and content[start] > number and content[start] <= 89:
                number = content[start]
                if self.type == 1 and number == 89:
                    break
                function = [self.get_max_length, self.get_imp_class_uid, self.get_asy_op_win,
                            self.get_role_select, self.get_imp_ver_name, self.get_sop_ext_neg,
                            self.get_sop_class_com_ext_neg, self.get_rq_user_id_user, 
                            self.get_ac_user_id_neg]
                start = function[number - 81](start, content)
                
            return startByte
        else:
            self.error_control('get_user_info')
            return begin
    
    def get_max_length(self, begin, content):
        if not self.write_database:
            return self.size
        length, max_content, startByte = self.mini_general(begin, content, len(content))
        if length == None:
            return begin
        elif length == 4:
            current = MaximumLengthSubitem()
            current.pdu_type = self.type
            current.item_length = length
            current.maximum_length_received = self.byte2number(max_content)
            self.subitem.append(current)
            return startByte
        else:
            self.error_control('get_max_length length != 4')
            return startByte

    def get_imp_class_uid(self, begin, content):
        if not self.write_database:
            return self.size
        length, imp_content, startByte = self.mini_general(begin, content, len(content))
        if length == None:
            return startByte
        else:
            current = ImplementationClassUidSubitem()
            current.pdu_type = self.type
            current.item_length = length
            current.implementation_class_uid = ''.join(chr(x) for x in imp_content)
            self.subitem.append(current)
            return startByte
    
    def get_asy_op_win(self, begin, content):
        if not self.write_database:
            return self.size
        length, asy_content, startByte = self.mini_general(begin, content, len(content))
        if length == None:
            return startByte
        elif length == 4:
            current = AsynchronousOperationWindowSubitem()
            current.item_length = length
            current.maximum_number_operations_invoked = ''.join(chr(x) for x in as_content[0,2])
            current.maximum_number_operations_performed = ''.join(chr(x) for x in as_content[2, 4])
            self.subitem.append(current)
            return startByte
        else:
            self.error_control('get_asy_op_win')
            return startByte
    
    def get_role_select(self, begin, content):
        if not self.write_database:
            return self.size
        length, role_content, startByte = self.mini_general(begin, content, len(content))
        if length == None:
            return startByte
        else:
            current = ScpScuRoleSelectionSubitem()
            current.pdu_type = self.type
            current.item_length = length
            uid_length, uid_content, endByte = self.mini_general(-2, role_content, len(role_content))
            if uid_length == None:
                return startByte
            else:
                current.uid_length = uid_length
                current.sop_class_uid = ''.join(chr(x) for x in uid_content)
                if length > endByte + 1:
                    current.scu_role = role_content[endByte]
                    current.scp_role = role_content[endByte + 1]
                    self.subitem.append(current)
                    return startByte
                else:
                    self.error_control('get_role_select length > endByte + 1')
                    return startByte
    
    def get_imp_ver_name(self, begin, content):
        if not self.write_database:
            return self.size
        length, imp_content, startByte = self.mini_general(begin, content, len(content))
        if length == None:
            return startByte
        else:
            current = ImplementationVersionNameSubitem()
            current.pdu_type = self.type
            current.item_length = length
            current.implementation_version_name = ''.join(chr(x) for x in imp_content)
            self.subitem.append(current)
            return startByte

    def get_sop_ext_neg(self, begin, content):
        if not self.write_database:
            return self.size
        length, sop_content, startByte = self.mini_general(begin, content. len(content)) 
        if length == None:
            return startByte
        else:
            current = SopClassExtendNegotiationSubitem()
            current.pdu_type = self.type
            current.item_length = length
            uid_length, uid_content, endByte = self.mini_general(-2, sop_content, len(sop_content))
            if uid_length == None:
                return startByte
            else:
                current.uid_length = uid_length
                current.sop_class_uid = ''.join(chr(x) for x in uid_content)
                if length > endByte:
                    current.service_class_application_information = ''.join(chr(x) for x in sop_content[endByte:])
                    self.subitem.append(current)
                    return startByte
                else:
                    self.error_control('get_sop_ext_neg length > endByte')
                    return startByte

    def get_sop_class_com_ext_neg(self, begin, content):
        if not self.write_database:
            return self.size
        length, sop_content, startByte = self.mini_general(begin, content, len(content))
        if length == None:
            return startByte
        else:
            current = SopClassCommonExtendNegotiationSubitem()
            current.subitem_version = content[begin+1]
            current.item_length = length
            uid_length, uid_content, endByte = self.mini_general(-2, sop_content, len(sop_content))
            if uid_length == None:
                return startByte
            else:
                current.sop_class_uid_length = uid_length
                current.sop_class_uid = ''.join(chr(x) for x in uid_content)
                service_length, service_content, serviceEndByte = self.mini_general(endByte - 2, sop_content, len(sop_content))
                if service_length == None:
                    return startByte
                else:
                    current.service_class_uid_length = service_length
                    current.service_class_uid = ''.join(chr(x) for x in service_content)
                    idLength, idContent, idByte = self.mini_general(serviceEndByte - 2, sop_content, len(sop_content))
                    if idLength == None:
                        return startByte
                    start = 0
                    while idLength > 0:
                        # 此处的general_length等是否需要单独建表(有点记不清了)
                        general_length, general_content, start = self.mini_general(start, idContent, len(idContent))
                        if general_length == None:
                            return startByte
                        current.realted_general_sop_class_uid_length = general_length
                        current.realted_general_sop_class_uid = ''.join(chr(x) for x in general_content)
                    self.subitem.append(current)
                    return startByte
    
    def get_rq_user_id_user(self, begin, content):
        if not self.write_database:
            return self.size
        length, rq_content, startByte = self.mini_general(begin, content, len(content))
        if length == None:
            return startByte
        current = UserIdentityNegotiationSubitemRQ()
        current.item_length = length
        current.user_identity_type = rq_content[0]
        current.positive_response_requested = rq_content[1]
        filed_length, filed_content, endByte = self.mini_general(0, rq_content, length)
        if filed_length == None:
            return startByte
        current.primary_field_length = filed_length
        current.primary_field = ''.join(chr(x) for x in filed_content)
        second_length, second_content, second_byte = self.mini_general(endByte, rq_content, length)
        if second_length == None:
            return startByte
        current.second_field_length = second_length
        current.second_field = ''.join(chr(x) for x in second_content)
        self.subitem.append(current)
        return startByte
    
    def get_ac_user_id_neg(self, begin, content):
        if not self.write_database:
            return self.size
        length, ac_content, startByte = self.mini_general(begin, content, len(content))
        if length == None:
            return startByte
        current = UserIdentityNegotiationSubitemAC()
        current.pdu_type = self.type
        current.item_length = length
        server_length, server_content, server_byte = self.mini_general(-2, ac_content, length)
        if server_length == None:
            return startByte
        current.server_response_length = server_length
        current.server_response = ''.join(chr(x) for x in server_content)
        self.subitem.append(current)
        return startByte

    def brunch1(self):
        self.type = 1
        self.result = AAssociateRQ()
        self.get_pdu_length()
        self.get_version()
        self.get_target_name()
        self.get_source_name()
        self.judge75()
        self.get_a_context()
        startByte = self.result.a_context_length + 78
        while self.data[startByte] == 32 and self.write_database:
            startByte = self.get_p_context(startByte)
            if startByte >= self.size:
                self.error_control('brunch1 32 startByte >= self.size')
            pass
        return self.get_user_info(startByte)
        pass
    
    def get_acp_context(self, begin):
        if not self.write_database:
            return self.size
        if self.data[begin] == 33:
            length, content, startByte = self.general(begin)
            if length == None:
                return startByte
            self.result.p_context_length = length
            self.result.p_context_id = content[0]
            self.result.result_reason = content[2]
            if content[2] == 0:
                if content[4] != 64:
                    self.error_control('get_acp_context content[4] != 64')
                ts_length, ts_content, endByte = self.mini_general(4, content, length)
                current = TransferSyntaxSubitem()
                current.ts_length = ts_length
                current.pdu_type = self.type
                current.item_length = ts_length
                current.ts_name = ''.join(chr(x) for x in ts_content)
                self.subitem.append(current)
            return startByte
        else:
            self.error_control('get_acp_context. self.data[begin] == 33')
            return begin
    
    def brunch2(self):
        self.type = 2
        self.result = AAssociateAC()
        self.get_pdu_length()
        self.get_version()
        self.judge75()
        self.get_a_context()
        startByte = self.get_acp_context(self.result.a_context_length + 78)
        return self.get_user_info(startByte)

    def brunch3(self):
        self.type = 3
        self.result = AAssociateRJ()
        self.get_pdu_length()
        if self.size >= 10:
            self.result.result = self.data[7]
            self.result.source = self.data[8]
            self.result.reason_diag = self.data[9]
            return self.size
        else:
            self.error_control('brunch3 size >= 10')
            return self.size
        pass
    
    # 此处pdv长度有可能过长，暂时采用普通方式处理
    def get_pdv(self, startByte, number):
        current = PresentationDataValue()
        if startByte + 6 <= self.size:
            current.item_length = self.byte2number(
                self.data[startByte: startByte + 4])
            current.p_context_id = self.data[4]
            control_header = self.data[5]
            current.data_type = control_header & 1
            if control_header & 2 == 2:
                current.last_fragment = True
            else:
                current.last_fragment = False
            if current.item_length + startByte + 4 <= self.size:
                # pdv 长度过长时应当注意修改此处
                current.pdv_data = self.data[startByte +
                                             6: current.item_length + 6 + startByte]
                self.subitem.append(current)
                return self.size
            else:
                error_control('get_pdv current.item_length + starByte + 6')
                return self.size
        else:
            error_control('get_pdv startByte + 8')
            return self.size
    
    def brunch4(self):
        self.type = 4
        self.result = PDataTF()
        self.get_pdu_length()
        startByte = 6
        length = self.result.pdu_length
        i = 1
        while length > 0:
            lastPlace = startByte
            startByte = self.get_pdv(startByte, i)
            length = length - (startByte - lastPlace)
            i = i + 1
        return self.size
        pass

    def brunch5(self):
        self.type = 5
        self.result = AReleaseRQ()
        self.get_pdu_length()
        return self.size
        pass

    def brunch6(self):
        self.type = 6
        self.result = AReleaseRP()
        self.get_pdu_length()
        return self.size
        pass

    def brunch7(self):
        self.type = 7
        self.result = ABort()
        self.get_pdu_length()
        if self.size >= 10:
            self.result.source = self.data[8]
            self.result.reason_diag = self.data[9]
        else:
            self.error_control('brunch7 size >= 10')
        return self.size

    def byte2number(self, number):
        sum = 0
        for x in number:
            sum = sum*256 + x
        return sum
        pass


class FileReader:

    __fileSize__ = 1024*1024

    def __init__(self, filePath):
        if os.path.exists(filePath):
            self.file = open(filePath, 'rb')
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
