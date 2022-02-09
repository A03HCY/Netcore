import socket, struct, base64
import threading, queue
import platform, os, io
import random
import ast
import time
import re

__version__ = '1.0.3-beta'

SAFE_TIME = 5
OUT_TIME  = 15


def IsIP(str):
    p = re.compile('^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
    if p.match(str):return True
    else:return False


def RanCode(num):
    ran_str = ''.join(random.sample('abcdefghijklmnopqrstuvwxyz0123456789', num))
    return ran_str


def B64en(data):
    data = data.encode('utf-8')
    data = base64.b64encode(data).decode('utf-8')
    return data


def B64de(data):
    data = data.encode('utf-8')
    data = base64.b64decode(data).decode('utf-8')
    return data


class Cosi:
    def __init__(self, conn:socket.socket=None, mode:str='TCP', buffsize:int=2048) -> None:
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
    
    def __send(self, bytesdata=b'', address=None) -> None:
        if self.mode == 'UDP':
            self.conn.sendto(address, bytesdata)
            return
        elif self.mode == 'TCP':
            length = len(bytesdata)
            header = struct.pack('i', length)
            self.conn.send(header)
            self.conn.send(bytesdata)
            return
        
    def send(self, bytesdata=b'', address=None) -> None:
        self.__send(bytesdata, address)
    
    def recv(self) -> bytes:
        if self.mode == 'UDP':
            bytesdatarray = self.conn.recvfrom()
            return bytesdatarray
        elif self.mode == 'TCP':
            header = self.conn.recv(4)
            length = struct.unpack('i', header)[0]
            bytesdata = b''
            while length > self.buff:
                bytesdata += self.conn.recv(self.buff)
                length -= self.buff
            bytesdata += self.conn.recv(length)
            return bytesdata
    
    def connect(self, address) -> None:
        self.conn.connect(address)
    
    def bind(self, address) -> None:
        self.conn.bind(address)
    
    def close(self) -> None:
        self.conn.close()