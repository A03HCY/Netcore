from base64 import b64encode, b64decode
from io import BytesIO
from random import sample
from struct import pack
from re import compile

__version__ = '202202.2120'


def IsIP(str):
    p = compile('^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
    if p.match(str):return True
    else:return False


def RanCode(num):
    ran_str = ''.join(sample('abcdefghijklmnopqrstuvwxyz0123456789', num))
    return ran_str


def B64en(data):
    data = data.encode('utf-8')
    data = b64encode(data).decode('utf-8')
    return data


def B64de(data):
    data = data.encode('utf-8')
    data = b64decode(data).decode('utf-8')
    return data


class Protocol:
    def __init__(self, meta_data, type_code:int=0, content_code:int=0):
        self.meta = meta_data
        self.type_code = type_code
        self.cont_code = content_code
    
    def GetHead(self, length:int=None):
        iden_code = bytes( [self.type_code, self.cont_code] )
        if not length:length = len(self.meta)
        leng_code = pack('i', length)
        head_code = iden_code + leng_code
        return head_code
    
    def ReadHead(self, bytesdata:bytes):
        self.type_code = bytesdata[0]
        self.cont_code = bytesdata[1]