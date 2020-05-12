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


engine = create_engine(
    'mysql://root:99277299@127.0.0.1:3306/medical')
DBSession = sessionmaker(bind=engine)
