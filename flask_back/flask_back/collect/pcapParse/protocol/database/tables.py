from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, relation, sessionmaker
from sqlalchemy import *
from .constant import mysqllink
import datetime

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
    time = Column(DateTime, default=datetime.datetime.now)
    receiver_ip_port = Column(String)
    processing_id = Column(String)
    version = Column(String)
    message_time = Column(DateTime)
    size = Column(BIGINT)
    sender_tag = Column(Boolean)
    receiver_tag = Column(Boolean)
    
    def __getitem__(self, item):
        return self.__dict__[item]
    def __setitem__(self, key, value):
        self.__dict__[key] = value

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

    
    def __getitem__(self, item):
        return self.__dict__[item]
    def __setitem__(self, key, value):
        self.__dict__[key] = value

class MessageMain(Base):
    __tablename__ = 'message'  # 数据库表名

    id = Column(BIGINT, autoincrement=True, primary_key=True)
    send_ip_port = Column(String)
    receiver_ip_port = Column(String)
    complete_status = Column(String)
    seqnumber = Column(BIGINT)
    type = Column(String)
    size = Column(BIGINT)
    time = Column(DateTime, default=datetime.datetime.now)
    version = Column(String)
    dsc_status = Column(Boolean)
    sender_tag = Column(Boolean)
    receiver_tag = Column(Boolean)
    
    def __getitem__(self, item):
        return self.__dict__[item]
    def __setitem__(self, key, value):
        self.__dict__[key] = value

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
    
    def __getitem__(self, item):
        return self.__dict__[item]
    def __setitem__(self, key, value):
        self.__dict__[key] = value
    pass


class PatientInfo(Base):
    __tablename__='patient_info'

    id = Column(BIGINT, primary_key = True, autoincrement=True)
    time = Column(DateTime, default=datetime.datetime.now)
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
    size = Column(BIGINT)
    sender_tag = Column(Boolean)
    receiver_tag = Column(Boolean)

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

class CollectResult(Base):
    __tablename__ = 'collect_result'

    id = Column(BIGINT, primary_key=True)
    protocol = Column(String)
    port = Column(INT)
    time = Column(BIGINT)
    submit = Column(DATETIME, default=datetime.datetime.now)
    start_time = Column(DATETIME)
    end_time = Column(DATETIME)
    size = Column(BIGINT)
    
    def __getitem__(self, item):
        return self.__dict__[item]
    def __setitem__(self, key, value):
        self.__dict__[key] = value
    pass


engine = create_engine(
    'mysql://' + mysqllink)
DBSession = sessionmaker(bind=engine)
