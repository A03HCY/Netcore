'''
Copyright (c) 2021 https://gitee.com/intellen
Intellen - Network is licensed under Mulan PSL v2.
You can use this software according to the terms and conditions of the Mulan PSL v2. 
You may obtain a copy of Mulan PSL v2 at:
            http://license.coscl.org.cn/MulanPSL2 
THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.  
See the Mulan PSL v2 for more details. 

Url     : https://gitee.com/intellen/network
'''
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
WEB_DATA  = 'https://gitee.com/intellen/network/raw/docs/service.cot'


def LoadInfo(tar:str=WEB_DATA):
    import requests
    res = requests.get(tar)
    cot = io.StringIO(res.text)
    rel = {}
    for i in cot.readlines():
        i = i.strip().split('=')
        key = i[0].strip()
        val = i[1].strip()
        rel[key] = val
    return rel


def IsIP(str):
    p = re.compile('^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
    if p.match(str):return True
    else:return False


def RanCode(num):
    ran_str = ''.join(random.sample('abcdefghijklmnopqrstuvwxyz0123456789', num))
    return ran_str


def RanID():
    lis = [10,3,5]
    uid = ''
    for i in lis:
        uid += RanCode(i) + '-'
    return uid[:-1]


def B64en(data):
    data = data.encode('utf-8')
    data = base64.b64encode(data).decode('utf-8')
    return data


def B64de(data):
    data = data.encode('utf-8')
    data = base64.b64decode(data).decode('utf-8')
    return data


def Indexall(path, fo=False):
    if not os.path.isdir(path):
        return {}
    td = {'f':{},'d':{}}
    size = 0
    try:
        for i in os.listdir(path):
            p = os.path.join(path, i)
            i = B64en(i)
            if os.path.isfile(p):
                td['f'][i] = os.path.getsize(p)
                size += os.path.getsize(p)
                continue
            if os.path.isdir(p):
                if fo == True:
                    td['d'][i] = Indexall(p)
                else:
                    td['d'][i] = {}
                continue
    except:return {}
    if td['f'] == {}:del td['f']
    if td['d'] == {}:del td['d']
    return td


def Initall(data):
    if not type(data) == dict:return {}
    odata = {
        'f':{},
        'd':{}
    }
    if 'f' in data:
        for i in data['f']:
            d = B64de(i)
            odata['f'][d] = data['f'][i]
    if 'd' in data:
        for i in data['d']:
            d = B64de(i)
            odata['d'][d] = Initall(data['d'][i])
    if odata['f'] == {}:del odata['f']
    if odata['d'] == {}:del odata['d']
    return odata


def TotalSize(data):
    size = 0
    if data.get('f'):
        for d in data['f']:
            size += data['f'][d]
    if data.get('d'):
        for d in data['d']:
            size += TotalSize(data['d'][d])
    return size


class Consiver:
    def __init__(self, conn:socket.socket=None, mode:str='TCP', buffsize:int=2048) -> None:
        self.Idata = {}
        self.que = queue.Queue()
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


def CreatTree(address:tuple, password:str, uid:str=RanID()) -> Consiver:
    Tocon = Consiver()
    Tocon.connect(address)
    # Get and Send Info
    Tocon.save('_PWD', password)
    Tocon.save('uid', uid)
    Tocon.save('name', platform.node())
    Tocon.save('platform', platform.platform())
    Tocon.send(str(Tocon.Idata).encode('utf-8'))
    Tocon.save('addr', address)
    # Recv Result
    try:
        data = Tocon.recv().decode('utf-8')
    except:raise ConnectionRefusedError('Authentication Problem.')
    return Tocon