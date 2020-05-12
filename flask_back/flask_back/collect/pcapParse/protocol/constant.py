SB = b'\x0b'
EB = b'\x1c'
Field = 1
Component = 2
Repeat = 3
Escape = 4
Subcomponent = 5
HL7Separator = [b'\x0d', b'\x7c', b'\x5e', b'\x7e', b'\x5c', b'\x26']
HChar2Value = {
    3: 'message_id',
    4: 'password',
    5: 'sender',
    6: 'sender_address',
    8: 'sender_phone',
    9: 'sender_character',
    10: 'receiver_id',
    11: 'receiver_type_id',
    12: 'processing_id',
    13: 'version',
    14: 'message_time'
}
AstmSeparator = [b'\x0d', b'\x7c', b'\x5e', b'\x5c', b'\x26', b'\x00']
AstmDelimiterOrder = [Field, Repeat, Component, Escape]
TokenType = {
    'delitimter' : 0,
    'word': 1,
    'string' : 2, 
    'field' : 3,
    'other': 4,
    'start': 5,
    'end' : 6
}