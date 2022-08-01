from collections.abc import Iterable
import socket
import struct
import lzma
import json


VERS = 'alpha-202202.1219'
__version__ = VERS


def ReadHead(meta:bytes):
    type_code = meta[0]
    cont_code = meta[1]
    exps_data = list(meta[2:6])
    length = struct.unpack('i', meta[6:10])[0]
    return type_code, cont_code, exps_data, length


def check(meta):
    if not type(meta) == bytes:
        if not isinstance(meta,Iterable):meta = [meta]
        meta = bytes(meta)
    return meta


class BasicProtocol:
    def __init__(self, meta_data=None, type_code:int=255, content_code:int=255, exps_data:list=[0,0,0,0], line:bool=False):
        self.buff = None
        self.meta = meta_data
        self.type_code = type_code
        self.cont_code = content_code
        self.exps_data = exps_data
        self.line = line
    
    def GetHead(self, length:int=None):
        iden_code = bytes( [self.type_code, self.cont_code] )
        exps_code = bytes(self.exps_data)
        if not length:length = len(self.meta)
        leng_code = struct.pack('i', length)
        head_code = iden_code + exps_code + leng_code
        return head_code
    
    def GetFull(self):
        return self.GetHead() + self.meta
    
    def write(self, meta):
        meta = check(meta)
        if self.buff:
            self.buff += meta
        else:
            self.buff = meta
        
        if self.line:return self
    
    def load(self, force_load:bool=False, from_temp=None):
        if not from_temp:
            from_temp = self.buff
        try:
            # Load to temp
            type_code = from_temp[0]
            cont_code = from_temp[1]
            exps_code = from_temp[2:6]
            length = struct.unpack('i', from_temp[6:10])[0]
            meta = from_temp[10:]
        except:
            if self.line:
                return self
            else:
                return False
        
        # Comfirm head
        if not force_load:
            if length != len(from_temp[10:]):
                if self.line:return self
                else:return False
        
        # Save and clean
        self.type_code = type_code
        self.cont_code = cont_code
        self.exps_data = list(exps_code)
        self.meta = meta
        if not from_temp:
            self.buff = None

        if self.line:return self
        else:return True
    
    def compress(self):
        self.meta = lzma.compress(self.GetFull())
        self.type_code = 0
        self.cont_code = 1

        if self.line:return self
    
    def decompress(self, force_deco:bool=False, force_load:bool=False, meta_only:bool=False):
        if [self.type_code, self.cont_code] != [0, 1]:
            if not force_deco:
                if self.line:return self
                else:return False
        self.buff = None
        result = self.load(from_temp=lzma.decompress(self.meta), force_load=force_load)

        if self.line:return self
        else:return result
    
    def save(self, location:str, meta_only=False):
        with open(location, 'wb') as f:
            if meta_only:
                f.write(self.meta)
            else:
                f.write(self.GetFull())
        
        if self.line:return self


def LoadFile(location:str, meta_only:bool=False, line:bool=False):
    with open(location, 'rb') as f:
        if meta_only:
            org = BasicProtocol(f.read(), line=line)
        else:
            org = BasicProtocol(line=line)
            org.load(from_temp=f.read())
    return org


class Conet:
    def __init__(self, conn:socket.socket=None, mode:str='TCP', buffsize:int=2048):
        self.Idata = {}
        self.conn = conn
        self.mode = mode
        self.buff = buffsize
        if conn == None:
            if mode == 'TCP':
                self.conn = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            elif mode == 'UDP':
                self.conn = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    
    def save(self, key, val):
        self.Idata[key] = val
    
    def get(self, key):
        return self.Idata.get(key)
    
    def __send(self, bytesdata=b'', address=None):
        if self.mode == 'UDP':
            self.conn.sendto(address, bytesdata)
            return
        elif self.mode == 'TCP':
            self.conn.send(bytesdata)
            return
        
    def send(self, bytesdata=b'', address=None):
        self.__send(BasicProtocol(bytesdata, type_code=0, content_code=40, line=True).GetFull(), address)
    
    def force_send(self, bytesdata=b''):
        self.conn.send(bytesdata)
    
    def force_recv(self, num):
        return self.conn.recv(num)
    
    def recv(self, protocal=False, ans=False) -> bytes:
        if self.mode == 'UDP':
            bytesdatarray = self.conn.recvfrom()
            return bytesdatarray

        data = BasicProtocol()
        header = b''
        while len(header) < 10:
            header += self.conn.recv(1)

        length = ReadHead(header)[3]
        recvdata = b''
        while len(recvdata) < length:
            if length - len(recvdata) > self.buff:
                recvdata += self.conn.recv(self.buff)
            else:
                recvdata += self.conn.recv(length - len(recvdata))
        
        data.load(from_temp=header+recvdata, force_load=True)

        if protocal:return data
        else:return data.meta
    
    def recvdata(self):
        data = self.recv()
        data = data.decode('utf-8')
        data = json.loads(data)
        return data
    
    def sendata(self, data):
        data = json.dumps(data)
        data = data.encode('utf-8')
        self.send(data)
    
    def connect(self, address):
        self.conn.connect(address)
    
    def bind(self, address):
        self.conn.bind(address)
    
    def listen(self, num):
        self.conn.listen(num)
    
    def accept(self):
        client_socket, clientAddr = self.conn.accept()
        client_socket = Conet(client_socket, mode='TCP')
        return client_socket, clientAddr
    
    def close(self):
        self.conn.close()


def IPShow(ip):
    ip = list(ip)
    ip = '.'.join(list(map(str, ip)))
    return ip


def clearify(org, dic, defult=None):
    passable = True
    res = {}
    for i in dic:
        if not i in org:passable = False
        res[i] = org.get(i, defult)
    return res, passable