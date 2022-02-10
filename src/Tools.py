from collections.abc import Iterable
import struct


__version__ = '202202.2213'


def ReadHead(meta:bytes):
    type_code = meta[0]
    cont_code = meta[1]
    length = struct.unpack('i', meta[2:6])[0]
    return type_code, cont_code, length


def check(meta):
    if not type(meta) == bytes:
        if not isinstance(meta,Iterable):meta = [meta]
        meta = bytes(meta)
    return meta


class DataProtocol:
    def __init__(self, meta_data=None, type_code:int=0, content_code:int=0):
        self.buff = None
        self.meta = meta_data
        self.type_code = type_code
        self.cont_code = content_code
    
    def GetHead(self, length:int=None):
        iden_code = bytes( [self.type_code, self.cont_code] )
        if not length:length = len(self.meta)
        leng_code = struct.pack('i', length)
        head_code = iden_code + leng_code
        return head_code
    
    def write(self, meta):
        meta = check(meta)
        if self.buff:
            self.buff += meta
        else:
            self.buff = meta
    
    def done(self):
        try:
            self.type_code = self.buff[0]
            self.cont_code = self.buff[1]
            length = struct.unpack('i', self.buff[2:6])[0]
        except:return False
        if length != len(self.buff[6:]):return False
        self.meta = self.buff[6:]
        self.buff = None
        return True