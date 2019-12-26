from flask_back import db

class AAssociateRQ(db.Model):
    __tablename__ = 'a_associate_rq' #数据库表名

    id = db.Column(db.BIGINT, autoincrement=True, primary_key=True)
    time = db.Column(db.DateTime, default=db.TIMESTAMP)
    pdu_length = db.Column(db.INT)
    protocol_version = db.Column(db.String)
    called_ae_title = db.Column(db.String)
    calling_ae_title = db.Column(db.String)
    a_context_length = db.Column(db.INT)
    a_context_name = db.Column(db.String)
    user_info_length = db.Column(db.INT)
    send_ip_port = db.Column(db.String)
    receive_ip_port = db.Column(db.String)

class PContext(db.Model):
    __tablename__ = 'p_context'
    pdu_id = db.Column(db.BIGINT, primary_key=True)
    pdu_type = db.Column(db.INT, primary_key=True)
    p_context_length = db.Column(db.INT)
    p_context_id = db.Column(db.INT)
    as_length = db.Column(db.INT)
    as_name = db.Column(db.String)

class TransferSyntaxSubitem(db.Model):
    __tablename__ = 'tansfer_syntax_subitem'
    pdu_id = db.Column(db.BIGINT)
    pdu_type = db.Column(db.INT)
    ts_id = db.Column(db.INT, autoincrement=True, primary_key=True)   # 主键问题
    p_context_id = db.Column(db.INT)
    ts_length = db.Column(db.INT)
    ts_name = db.Column(db.String)

class MaximumLengthSubitem(db.Model):
    __tablename__ = 'maximum_length_subitem'
    pdu_id = db.Column(db.BIGINT, primary_key=True)
    pdu_type = db.Column(db.INT, primary_key=True)
    item_length = db.Column(db.INT)
    maximum_length_received = db.Column(db.INT)


class ImplementationClassUidSubitem(db.Model):
    __tablename__ = 'implementation_class_uid_subitem'
    pdu_id = db.Column(db.BIGINT, primary_key=True)
    pdu_type = db.Column(db.INT, primary_key=True)
    item_length = db.Column(db.INT)
    implementation_class_uid = db.Column(db.String)


class AsynchronousOperationWindowSubitem(db.Model):
    __tablename__ = 'asynchronous_operations_window_subitem'
    pdu_id = db.Column(db.BIGINT, primary_key=True)
    pdu_type = db.Column(db.INT, primary_key=True)
    item_length = db.Column(db.INT)
    maximum_number_operations_invoked = db.Column(db.INT)
    maximum_number_operations_performed = db.Column(db.INT)

class ScpScuRoleSelectionSubitem(db.Model):
    __tablename__ = 'scp_scu_role_selection_subitem'
    pdu_id = db.Column(db.BIGINT, primary_key=True)
    pdu_type = db.Column(db.INT, primary_key=True)
    item_length = db.Column(db.INT)
    uid_length = db.Column(db.INT)
    sop_class_uid = db.Column(db.String)
    scu_role = db.Column(db.INT)
    scp_role = db.Column(db.INT)


class ImplementationVersionNameSubitem(db.Model):
    __tablename__ = 'implementation_version_name_subitem'
    pdu_id = db.Column(db.BIGINT, primary_key=True)
    pdu_type = db.Column(db.INT, primary_key=True)
    item_length = db.Column(db.INT)
    implementation_version_name = db.Column(db.String)


class SopClassExtendedNegotiationSubitem(db.Model):
    __tablename__ = 'sop_class_extended_negotiation_subitem'
    pdu_id = db.Column(db.BIGINT, primary_key=True)
    pdu_type = db.Column(db.INT, primary_key=True)
    item_length = db.Column(db.INT)
    implementation_version_name = db.Column(db.String)
    sop_class_uid_length = db.Column(db.INT)
    sop_class_uid = db.Column(db.String)
    service_class_application_information = db.Column(db.String)


# class SopClassCommonExtendedNegotiationSubitem(db.model):
#     __tablename__ = 'sop_class_common_extended_negotiation_subitem'
#     pdu_id = db.Column(db.BIGINT, primary_key=True)
#     pdu_type = db.Column(db.INT, primary_key=True)
#     subitem_version = db.Column(db.String)
#     item_length = db.Column(db.INT)
#     sop_class_uid_length = db.Column(db.INT)
#     sop_class_uid = db.Column(db.String)
#     service_class_uid_length = db.Column(db.INT)
#     service_class_uid = db.Column(db.String)
#     related_general_sop_class_identification_length = db.Column(db.INT)
#     related_general_sop_class_uid_length = db.Column(db.INT)
#     related_general_sop_class_uid = db.Column(db.String)


class SopClassCommonExtendedNegotiationSubitem(db.Model):
    __tablename__ = 'sop_class_common_extended_negotiation_subitem'
    id = db.Column(db.BIGINT, autoincrement=True, primary_key=True)
    pdu_id = db.Column(db.BIGINT)
    pdu_type = db.Column(db.INT)
    subitem_version = db.Column(db.String)
    item_length = db.Column(db.INT)
    sop_class_uid_length = db.Column(db.INT)
    sop_class_uid = db.Column(db.String)
    service_class_uid_length = db.Column(db.INT)
    service_class_uid = db.Column(db.String)


class SopClassCommonSubitem(db.Model):
    __tablename__ = 'sop_class_common_subitem'

    id = db.Column(db.BIGINT, autoincrement = True, primary_key=True)
    sop_com_id = db.Column(db.BIGINT)
    related_general_sop_class_identification_length = db.Column(db.INT)
    related_general_sop_class_uid_length = db.Column(db.INT)
    related_general_sop_class_uid = db.Column(db.String)


class UserIdentityNegotiationSubitemRQ(db.Model):
    __tablename__ = 'user_identity_negotiation_subitem_rq'
    pdu_id = db.Column(db.BIGINT, primary_key=True)
    pdu_type = db.Column(db.INT, primary_key=True)
    item_length = db.Column(db.INT)
    user_identity_type = db.Column(db.INT)
    positive_response_requested = db.Column(db.INT)
    primary_field_length = db.Column(db.INT)
    primary_field = db.Column(db.String)
    secondary_field_length = db.Column(db.INT)
    secondary_field = db.Column(db.String)


class AAssociateAC(db.Model):
    __tablename__ = 'a_associate_ac'  # 数据库表名

    id = db.Column(db.BIGINT, autoincrement=True, primary_key=True)
    time = db.Column(db.DateTime, default=db.TIMESTAMP)
    pdu_length = db.Column(db.INT)
    protocol_version = db.Column(db.String)
    a_context_length = db.Column(db.INT)
    a_context_name = db.Column(db.String)
    p_context_length = db.Column(db.INT)
    p_context_id = db.Column(db.INT)
    result_reason = db.Column(db.INT)
    user_info_length = db.Column(db.INT)
    send_ip_port = db.Column(db.String)
    receive_ip_port = db.Column(db.String)


class UserIdentityNegotiationSubitemAC(db.Model):
    __tablename__ = 'user_identity_negotiation_subitem_ac'
    pdu_id = db.Column(db.BIGINT, primary_key=True)
    pdu_type = db.Column(db.INT, primary_key=True)
    item_length = db.Column(db.INT)
    server_response_length = db.Column(db.INT)
    server_response = db.Column(db.String)


class AAssociateRJ(db.Model):
    __tablename__ = 'a_associate_rj'  # 数据库表名

    id = db.Column(db.INT, autoincrement=True, primary_key=True)
    time = db.Column(db.DateTime, default=db.TIMESTAMP)
    pdu_length = db.Column(db.INT)
    result = db.Column(db.INT)
    source = db.Column(db.INT)
    reason_diag = db.Column(db.INT)
    send_ip_port = db.Column(db.String)
    receive_ip_port = db.Column(db.String)


class AReleaseRQ(db.Model):
    __tablename__ = 'a_release_rq'  # 数据库表名

    id = db.Column(db.INT, autoincrement=True, primary_key=True)
    time = db.Column(db.DateTime, default=db.TIMESTAMP)
    pdu_length = db.Column(db.INT)
    send_ip_port = db.Column(db.String)
    receive_ip_port = db.Column(db.String)


class AReleaseRP(db.Model):
    __tablename__ = 'a_release_rp'  # 数据库表名

    id = db.Column(db.INT, autoincrement=True, primary_key=True)
    time = db.Column(db.DateTime, default=db.TIMESTAMP)
    pdu_length = db.Column(db.INT)
    send_ip_port = db.Column(db.String)
    receive_ip_port = db.Column(db.String)


class ABort(db.Model):
    __tablename__ = 'a_bort'  # 数据库表名

    id = db.Column(db.INT, autoincrement=True, primary_key=True)
    time = db.Column(db.DateTime, default=db.TIMESTAMP)
    pdu_length = db.Column(db.INT)
    source = db.Column(db.INT)
    reason_diag = db.Column(db.INT)
    send_ip_port = db.Column(db.String)
    receive_ip_port = db.Column(db.String)

class PDataTF(db.Model):
    __tablename__ = 'p_data_tf'  # 数据库表名

    id = db.Column(db.INT, autoincrement=True, primary_key=True)
    time = db.Column(db.DateTime, default=db.TIMESTAMP)
    pdu_length = db.Column(db.INT)
    send_ip_port = db.Column(db.String)
    receive_ip_port = db.Column(db.String)

class PresentationDataValue(db.Model):
    __tablename__ = 'presentation_data_value'  # 数据库表名

    pdu_id = db.Column(db.BIGINT)
    pdv_id = db.Column(db.INT, autoincrement=True, primary_key=True)
    item_length = db.Column(db.INT)
    p_context_id = db.Column(db.INT)
    last_fragment = db.Column(db.Boolean)
    data_type = db.Column(db.INT)
    pdv_data = db.Column(db.String)


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


class Fragment(db.Model):
    __tablename__ = 'fragment'  # 数据库表名
    # id = relationship("MessageMain", backref="segment",
    #                   order_by="MessageMain.message_id", primary_key=True)
    id = db.Column(db.BIGINT, primary_key=True)
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

class RuleHttp(db.Model):
    __tablename__ = 'rule_http'

    id = db.Column(db.BIGINT, primary_key=True)
    value = db.Column(db.String)
    pass

class CollectResult(db.Model):
    __tablename__ = 'collect_result'

    id = db.Column(db.BIGINT, primary_key=True)
    protocol = db.Column(db.String)
    port = db.Column(db.INT)
    time = db.Column(db.BIGINT)
    submit = db.Column(db.DATETIME)
    start_time = db.Column(db.DATETIME)
    end_time = db.Column(db.DATETIME)
    size = db.Column(db.INT)
    pass

class MonitorRule(db.Model):
    __tablename__ = 'monitor_rule'

    id = db.Column(db.BIGINT, primary_key=True, autoincrement=True)
    ip = db.Column(db.String)
    # port = db.Column(db.INT)

class MonitorResult(db.Model):
    __tablename__ = 'monitor_result'

    id = db.Column(db.BIGINT, primary_key=True)
    rule_id = db.Column(db.BIGINT)
    src_ip = db.Column(db.String)
    src_port = db.Column(db.INT)
    dst_ip = db.Column(db.String)
    dst_port = db.Column(db.INT)
    start_time = db.Column(db.DATETIME)
    content = db.Column(db.BLOB)
    trans_size = db.Column(db.INT)
#
class ActiveFindIp(db.Model):
    __tablename__ = 'active_find_ip'

    id = db.Column(db.BIGINT, primary_key=True)
    ip = db.Column(db.String)
    port = db.Column(db.INT)

class ActiveResult(db.Model):
    __tablename__ = 'active_result'

    id = db.Column(db.BIGINT, primary_key=True)
    active_ip_id = db.Column(db.BIGINT)
    src_ip = db.Column(db.String)
    src_port = db.Column(db.INT)
    dst_ip = db.Column(db.String)
    dst_port = db.Column(db.INT)
    time = db.Column(db.BIGINT)

class Logs(db.Model):
    __tablename__ = 'logs'

    id = db.Column(db.BIGINT, primary_key=True)
    ip = db.Column(db.String)
    port = db.Column(db.INT)
    type = db.Column(db.INT)
    submit_json = db.Column(db.TEXT)
    response_json = db.Column(db.TEXT)
    create_date = db.Column(db.DATETIME)

class IPPostition(db.Model):
    __tablename__ = 'ip_postition'

    id = db.Column(db.BIGINT, primary_key=True)
    src_ip = db.Column(db.String)
    submit_ip = db.Column(db.String)
    submit_time = db.Column(db.DATETIME)
    equipment = db.Column(db.String)
    address = db.Column(db.String)
    institution = db.Column(db.String)