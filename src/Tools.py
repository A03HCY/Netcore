from collections.abc import Iterable
import struct
import lzma


__version__ = '202202.1021'


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


class BasicProtocol:
    def __init__(self, meta_data=None, type_code:int=255, content_code:int=255):
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
    
    def GetFull(self):
        return self.GetHead() + self.meta
    
    def write(self, meta):
        meta = check(meta)
        if self.buff:
            self.buff += meta
        else:
            self.buff = meta
    
    def load(self, force:bool=False, from_temp=None):
        if not from_temp:
            from_temp = self.buff
        try:
            # Load to temp
            type_code = from_temp[0]
            cont_code = from_temp[1]
            meta = from_temp[6:]
            length = struct.unpack('i', from_temp[2:6])[0]
        except:
            return False
        # Comfirm head
        if length != len(from_temp[6:]):
            if not force:return False
        # Save and clean
        self.type_code = type_code
        self.cont_code = cont_code
        self.meta = meta
        if not from_temp:
            self.buff = None
        return True
    
    def compress(self):
        self.meta = lzma.compress(self.GetFull())
        self.type_code = 0
        self.cont_code = 1
    
    def decompress(self, force_deco:bool=False, force_load:bool=False):
        if [self.type_code, self.cont_code] != [0, 1]:
            if not force_deco:return False
        self.buff = None
        result = self.load(from_temp=lzma.decompress(self.meta), force=force_load)
        return result
    
    def save(self, location:str, meta_only=False):
        with open(location, 'wb') as f:
            if meta_only:
                f.write(self.meta)
            else:
                f.write(self.GetFull())


def LoadFile(location:str, meta_only:bool=False):
    with open(location, 'rb') as f:
        if meta_only:
            org = BasicProtocol(f.read())
        else:
            org = BasicProtocol()
            org.load(from_temp=f.read())
    return org