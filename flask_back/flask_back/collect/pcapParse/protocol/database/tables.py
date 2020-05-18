from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, relation, sessionmaker
from sqlalchemy import *

Base = declarative_base()


class AstmMain(Base):
    __tablename__ = 'astm_main'

    id = Column(BIGINT, autoincrement=True, primary_key=True)
    delimiter = Column(String)
    message_id = Column(String)
    password = Column(String)
    sender = Column(String)
    sender_address = Column(String)
    type = Column(String)
    sender_phone = Column(String)
    sender_character = Column(String)
    send_ip_port = Column(String)
    receiver = Column(String)
    receiver_id = Column(String)
    receiver_type_id = Column(String)
    receiver_ip_port = Column(String)
    processing_id = Column(String)
    version = Column(String)
    message_time = Column(DateTime)

    # def keys(self):
    #     return ('id','delimiter','message_id','password','sender','sender_address','type','sender_phone','sender_character','send_ip_port','receiver','receiver_type_id','receiver_ip_port','processing_id','version','message_time')

    # a = {
    #     3: message_id,
    #     4: password,
    #     5: sender,
    #     6: sender_address,
    #     8: sender_phone,
    #     9: sender_character,
    #     10: receiver_id,
    #     11: receiver_type_id,
    #     12: processing_id,
    #     13: version,
    #     14: message_time
    # }

    # def __getitem__(self, item):
    #     if type(item) == int:
    #         return a[item]
    #     return None


class AstmRecord(Base):
    __tablename__ = 'astm_record'

    main_id = Column(BIGINT, primary_key=True)
    id = Column(INT)
    patient_id = Column(INT)
    order_id = Column(INT)
    type = Column(String)
    delimiter = Column(String)
    content = Column(TEXT)
    p_continue = Column(Boolean)
    o_continue = Column(Boolean)
    _continue = Column(Boolean)

class MessageMain(Base):
    __tablename__ = 'message'  # 数据库表名

    id = Column(BIGINT, autoincrement=True, primary_key=True)
    send_ip_port = Column(String)
    receiver_ip_port = Column(String)
    complete_status = Column(String)
    seqnumber = Column(BIGINT)
    type = Column(String)
    size = Column(BIGINT)
    time = Column(DateTime)
    version = Column(String)
    dsc_status = Column(Boolean)

    pass


class Segment(Base):
    __tablename__ = 'segment'  # 数据库表名

    # id = relationship("MessageMain", backref="segment",
    #                   order_by="MessageMain.id", primary_key=True)
    id = Column(BIGINT, primary_key=True)
    seq = Column(INT, primary_key=True)
    delimiter = Column(String)
    name = Column(String)
    add_status = Column(Boolean)
    content = Column(Text)

    pass

class Fragment(Base):
    __tablename__ = 'fragment'  # 数据库表名
    # id = relationship("MessageMain", backref="segment",
    #                   order_by="MessageMain.message_id", primary_key=True)
    id = Column(BIGINT, primary_key=True)
    pass

class AAssociateRQ(Base):
    __tablename__ = 'a_associate_rq' #数据库表名

    id = Column(BIGINT, autoincrement=True, primary_key=True)
    pdu_length = Column(INT)
    protocol_version = Column(String)
    called_ae_title = Column(String)
    calling_ae_title = Column(String)
    a_context_length = Column(INT)
    a_context_name = Column(String)
    user_info_length = Column(INT)

class PContext(Base):
    __tablename__ = 'p_context'
    pdu_id = Column(BIGINT, primary_key=True)
    pdu_type = Column(INT, primary_key=True)
    p_context_length = Column(INT)
    p_context_id = Column(INT)
    as_length = Column(INT)
    as_name = Column(String)

class TransferSyntaxSubitem(Base):
    __tablename__ = 'tansfer_syntax_subitem'
    pdu_id = Column(BIGINT)
    pdu_type = Column(INT)
    ts_id = Column(INT, autoincrement=True, primary_key=True)   # 主键问题
    p_context_id = Column(INT)
    ts_length = Column(INT)
    ts_name = Column(String)

class MaximumLengthSubitem(Base):
    __tablename__ = 'maximum_length_subitem'
    pdu_id = Column(BIGINT, primary_key=True)
    pdu_type = Column(INT, primary_key=True)
    item_length = Column(INT)
    maximum_length_received = Column(INT)


class ImplementationClassUidSubitem(Base):
    __tablename__ = 'implementation_class_uid_subitem'
    pdu_id = Column(BIGINT, primary_key=True)
    pdu_type = Column(INT, primary_key=True)
    item_length = Column(INT)
    implementation_class_uid = Column(String)


class AsynchronousOperationWindowSubitem(Base):
    __tablename__ = 'asynchronous_operations_window_subitem'
    pdu_id = Column(BIGINT, primary_key=True)
    pdu_type = Column(INT, primary_key=True)
    item_length = Column(INT)
    maximum_number_operations_invoked = Column(INT)
    maximum_number_operations_performed = Column(INT)

class ScpScuRoleSelectionSubitem(Base):
    __tablename__ = 'scp_scu_role_selection_subitem'
    pdu_id = Column(BIGINT, primary_key=True)
    pdu_type = Column(INT, primary_key=True)
    item_length = Column(INT)
    uid_length = Column(INT)
    sop_class_uid = Column(String)
    scu_role = Column(INT)
    scp_role = Column(INT)


class ImplementationVersionNameSubitem(Base):
    __tablename__ = 'implementation_version_name_subitem'
    pdu_id = Column(BIGINT, primary_key=True)
    pdu_type = Column(INT, primary_key=True)
    item_length = Column(INT)
    implementation_version_name = Column(String)


class SopClassExtendedNegotiationSubitem(Base):
    __tablename__ = 'sop_class_extended_negotiation_subitem'
    pdu_id = Column(BIGINT, primary_key=True)
    pdu_type = Column(INT, primary_key=True)
    item_length = Column(INT)
    implementation_version_name = Column(String)
    sop_class_uid_length = Column(INT)
    sop_class_uid = Column(String)
    service_class_application_information = Column(String)


class SopClassCommonExtendedNegotiationSubitem(Base):
    __tablename__ = 'sop_class_common_extended_negotiation_subitem'
    pdu_id = Column(BIGINT, primary_key=True)
    pdu_type = Column(INT, primary_key=True)
    subitem_version = Column(String)
    item_length = Column(INT)
    sop_class_uid_length = Column(INT)
    sop_class_uid = Column(String)
    service_class_uid_length = Column(INT)
    service_class_uid = Column(String)
    related_general_sop_class_identification_length = Column(INT)
    related_general_sop_class_uid_length = Column(INT)
    related_general_sop_class_uid = Column(String)


# class SopClassCommonExtendedNegotiationSubitem(Base):
#     __tablename__ = 'sop_class_common_extended_negotiation_subitem'
#     id = Column(BIGINT, autoincrement=True, primary_key=True)
#     pdu_id = Column(BIGINT)
#     pdu_type = Column(INT)
#     subitem_version = Column(String)
#     item_length = Column(INT)
#     sop_class_uid_length = Column(INT)
#     sop_class_uid = Column(String)
#     service_class_uid_length = Column(INT)
#     service_class_uid = Column(String)


# class SopClassCommonSubitem(Base):
#     __tablename__ = 'sop_class_common_subitem'

#     related_general_sop_class_identification_length = Column(INT)
#     related_general_sop_class_uid_length = Column(INT)
#     related_general_sop_class_uid = Column(String)


class UserIdentityNegotiationSubitemRQ(Base):
    __tablename__ = 'user_identity_negotiation_subitem_rq'
    pdu_id = Column(BIGINT, primary_key=True)
    pdu_type = Column(INT, primary_key=True)
    item_length = Column(INT)
    user_identity_type = Column(INT)
    positive_response_requested = Column(INT)
    primary_field_length = Column(INT)
    primary_field = Column(String)
    secondary_field_length = Column(INT)
    secondary_field = Column(String)


class AAssociateAC(Base):
    __tablename__ = 'a_associate_ac'  # 数据库表名

    id = Column(BIGINT, autoincrement=True, primary_key=True)
    pdu_length = Column(INT)
    protocol_version = Column(String)
    a_context_length = Column(INT)
    a_context_name = Column(String)
    p_context_length = Column(INT)
    p_context_id = Column(INT)
    result_reason = Column(INT)
    user_info_length = Column(INT)


class UserIdentityNegotiationSubitemAC(Base):
    __tablename__ = 'user_identity_negotiation_subitem_ac'
    pdu_id = Column(BIGINT, primary_key=True)
    pdu_type = Column(INT, primary_key=True)
    item_length = Column(INT)
    server_response_length = Column(INT)
    server_response = Column(String)


class AAssociateRJ(Base):
    __tablename__ = 'a_associate_rj'  # 数据库表名

    id = Column(INT, autoincrement=True, primary_key=True)
    pdu_length = Column(INT)
    result = Column(INT)
    source = Column(INT)
    reason_diag = Column(INT)


class AReleaseRQ(Base):
    __tablename__ = 'a_release_rq'  # 数据库表名

    id = Column(INT, autoincrement=True, primary_key=True)
    pdu_length = Column(INT)


class AReleaseRP(Base):
    __tablename__ = 'a_release_rp'  # 数据库表名

    id = Column(INT, autoincrement=True, primary_key=True)
    pdu_length = Column(INT)


class ABort(Base):
    __tablename__ = 'a_bort'  # 数据库表名

    id = Column(INT, autoincrement=True, primary_key=True)
    pdu_length = Column(INT)
    source = Column(INT)
    reason_diag = Column(INT)

class PDataTF(Base):
    __tablename__ = 'p_data_tf'  # 数据库表名

    id = Column(INT, autoincrement=True, primary_key=True)
    pdu_length = Column(INT)

class PresentationDataValue(Base):
    __tablename__ = 'presentation_data_value'  # 数据库表名

    pdu_id = Column(BIGINT)
    pdv_id = Column(INT, autoincrement=True, primary_key=True)
    item_length = Column(INT)
    p_context_id = Column(INT)
    last_fragment = Column(BOOLEAN)
    data_type = Column(INT)
    pdv_data = Column(String)

class PatientInfo(Base):
    __tablename__='patient_info'

    id = Column(BIGINT, primary_key = True, autoincrement=True)
    patient_name = Column(String)
    send_ip_port = Column(String)
    receiver_ip_port = Column(String)
    patient_sex = Column(String)
    patient_age = Column(String)
    patient_birth_date = Column(String)
    patient_birth_time = Column(String)
    patient_weight = Column(Float)
    patient_id = Column(String)
    # patient_address = Column(String)
    patient_pregnancy_status = Column(INT) #怀孕状态

    def __getitem__(self, item):
        return self.__dict__[item]
    def __setitem__(self, key, value):
        self.__dict__[key] = value

class ImageInfo(Base):
    __tablename__ = 'image_info'

    id = Column(BIGINT, primary_key=True)
    sop_instance_id = Column(String)
    image_date = Column(String)
    image_time = Column(String)
    high_bit = Column(String)  #高位
    window_center = Column(String)  #窗位
    window_width = Column(String)   #窗款
    image_path = Column(String)

    def __getitem__(self, item):
        return self.__dict__[item]
    def __setitem__(self, key, value):
        self.__dict__[key] = value

class SeriesInfo(Base):
    __tablename__ = 'series_info'

    id = Column(BIGINT, primary_key=True)
    series_num = Column(String)
    series_instance_id = Column(String)
    study_modality = Column(String)
    series_description = Column(String)
    series_date = Column(String)
    series_time = Column(String)
    slice_thickness = Column(String)  #层厚
    spacing_between_slices = Column(String) #层与层之间的间距，单位mm
    slice_location = Column(String) #实际的相对位置，单位mm

    def __getitem__(self, item):
        return self.__dict__[item]
    def __setitem__(self, key, value):
        self.__dict__[key] = value

class StudyInfo(Base):
    __tablename__ = 'study_info'

    id = Column(BIGINT, primary_key=True)
    study_ris_id = Column(String) #检查号
    study_id = Column(String)
    study_instance_id = Column(String)
    study_date = Column(String)
    study_time = Column(String)
    study_body_part = Column(String) #检查部位
    study_description = Column(String)

    def __getitem__(self, item):
        return self.__dict__[item]
    def __setitem__(self, key, value):
        self.__dict__[key] = value

engine = create_engine(
    'mysql://root:99277299@127.0.0.1:3306/medical')
DBSession = sessionmaker(bind=engine)
