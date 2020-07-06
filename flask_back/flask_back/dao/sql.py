from flask_back import db
import datetime

class MessageMain(db.Model):
    __tablename__ = 'message'  # 数据库表名

    id = db.Column(db.BIGINT, autoincrement=True, primary_key=True)
    send_ip_port = db.Column(db.String)
    receive_ip_port = db.Column(db.String)
    complete_status = db.Column(db.Boolean)
    seqnumber = db.Column(db.INT)
    type = db.Column(db.String)
    time = db.Column(db.DateTime, default=db.TIMESTAMP)
    version = db.Column(db.String)
    dsc_status = db.Column(db.Boolean)
    sender_tag = db.Column(db.Boolean)
    receiver_tag = db.Column(db.Boolean)
    pass


class Segment(db.Model):
    __tablename__ = 'segment'  # 数据库表名

    # id = relationship("MessageMain", backref="segment",
    #                   order_by="MessageMain.id", primary_key=True)
    id = db.Column(db.BIGINT, primary_key=True)
    seq = db.Column(db.INT, primary_key=True)
    delimiter = db.Column(db.String)
    name = db.Column(db.String)
    add_status = db.Column(db.Boolean)
    content = db.Column(db.Text)

    pass

class RuleHl7(db.Model):
    __tablename__ = 'rule_hl7'

    id = db.Column(db.BIGINT, primary_key=True, autoincrement=True)
    value = db.Column(db.String)
    pass

class RuleDicom(db.Model):
    __tablename__ = 'rule_dicom'

    id = db.Column(db.BIGINT, primary_key=True)
    value = db.Column(db.INT)
    pass

class RuleAstm(db.Model):
    __tablename__ = 'rule_astm'

    id = db.Column(db.BIGINT, primary_key=True)
    value = db.Column(db.String)

class CollectResult(db.Model):
    __tablename__ = 'collect_result'

    id = db.Column(db.BIGINT, primary_key=True)
    protocol = db.Column(db.String)
    port = db.Column(db.INT)
    time = db.Column(db.BIGINT)
    submit = db.Column(db.DATETIME, default=datetime.datetime.now)
    start_time = db.Column(db.DATETIME)
    end_time = db.Column(db.DATETIME)
    size = db.Column(db.INT)
    pass

class MonitorRule(db.Model):
    __tablename__ = 'monitor_rule'

    id = db.Column(db.BIGINT, primary_key=True, autoincrement=True)
    ip = db.Column(db.String)

class Logs(db.Model):
    __tablename__ = 'logs'

    id = db.Column(db.BIGINT, primary_key=True)
    ip = db.Column(db.String)
    port = db.Column(db.INT)
    type = db.Column(db.INT)
    submit_json = db.Column(db.TEXT)
    response_json = db.Column(db.TEXT)
    create_date = db.Column(db.DATETIME, default=datetime.datetime.now)
