import struct


__version__ = '202202.2120'


def ReadHead(meta:bytes):
    type_code = meta[0]
    cont_code = meta[1]
    length = struct.unpack('i', meta[2:6])[0]
    return type_code, cont_code, length


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
    
    def Write(self, meta):
        if self.buff:
            self.buff + meta
        else:
            self.buff = meta
    
    def Done(self):
        self.type_code = self.buff[0]
        self.cont_code = self.buff[1]
        self.meta = self.buff[2:]
        self.buff = None
