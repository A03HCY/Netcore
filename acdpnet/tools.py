from collections.abc import Iterable
import socket
import struct
import queue
import lzma
import json
import random 
import string
import secrets
import os
import time

VERS = '2.2.1'
__version__ = VERS


def RanCode(num:int=4):
    res = ''.join(secrets.choice(string.ascii_letters + string.digits) for x in range(num))
    return res

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
        self.idf  = None
        self.que  = queue.Queue(maxsize=1)
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
            self.force_send(bytesdata)
            return
        
    def send(self, bytesdata=b'', address=None):
        self.__send(BasicProtocol(bytesdata, type_code=0, content_code=40, line=True).GetFull(), address)
    
    def force_send(self, bytesdata=b''):
        safe = RanCode(4)
        self.que.put(safe)
        self.conn.send(bytesdata)
        self.que.get()
        self.que.task_done()
    
    def force_recv(self, num):
        return self.conn.recv(num)
    
    def recv(self, protocal=False, ans=False) -> bytes:
        if self.mode == 'UDP':
            bytesdatarray = self.conn.recvfrom()
            return bytesdatarray

        data = BasicProtocol()
        header = b''
        while len(header) < 10:
            temp = self.conn.recv(1)
            header += temp
            if temp == b'':break

        length = ReadHead(header)[3]
        recvdata = b''
        while len(recvdata) < length:
            if length - len(recvdata) > self.buff:
                temp = self.conn.recv(self.buff)
                recvdata += temp
            else:
                temp = self.conn.recv(length - len(recvdata))
                recvdata += temp
            if temp == b'':break
        
        data.load(from_temp=header+recvdata, force_load=True)

        if protocal:return data
        else:return data.meta
    
    def recvdata(self, timeout=0):
        if timeout != 0:
            self.conn.settimeout(timeout)
            try:
                data = self.recv()
                data = data.decode('utf-8')
                data = json.loads(data)
            except:
                data = {}
            self.conn.setblocking(True)
            return data
        self.conn.setblocking(True)
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
        try:
            self.conn.shutdown(2)
            self.conn.close()
        except:pass


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


class List:
    def __init__(self, path:str, raw=False):
        self.path  = path
        self.raw   = raw
        self.table = []
        self.Do()
    
    def Do(self):
        path  = os.path.abspath(self.path)
        dirs  = []
        files = []
        for i in os.listdir(path):
            full = os.path.join(path, i)
            if os.path.isdir(full):
                dirs.append(i)
            elif os.path.isfile(full):
                files.append(i)
        for i in dirs:
            p = os.path.join(path, i)
            if self.raw:
                self.table.append(list(
                    (i, oct(os.stat(p).st_mode)[-3:], '-', 'D')
                ))
            else:
                self.table.append(list(
                    ("📁 "+i, oct(os.stat(p).st_mode)[-3:], self.time(p), '-')
                ))
        for i in files:
            p = os.path.join(path, i)
            if self.raw:
                size = os.path.getsize(p)
                self.table.append(list(
                    (i, oct(os.stat(p).st_mode)[-3:], size, 'F')
                ))
            else:
                size = self.convert_size(os.path.getsize(p))
                self.table.append(list(
                    ("📄 "+i, oct(os.stat(p).st_mode)[-3:], self.time(p), size)
                ))
    
    def convert_size(self, text):
        units = [" B", "KB", "MB", "GB", "TB", "PB"]
        size = 1024
        for i in range(len(units)):
            if (text/ size) < 1:
                return "%.2f %s" % (text, units[i])
            text = text/ size
    
    def time(self, path):
        data = time.localtime(os.stat(path).st_mtime)
        return time.strftime("%Y-%m-%d %H:%M", data)

class RemotePush:
    def __init__(self, data):
        self.size   = os.path.getsize(data['f_path'])
        self.prot   = BasicProtocol()
        self.header = self.prot.GetHead(length=self.size)
        self.data   = data

    def From(self, f):
        self.f = f
        return self

    def Now(self, conet):
        resp = {
            'command':'flow_trans',
            'data':self.data
        }
        conet.sendata(resp)
        conet.que.put(RanCode(4))
        conn = conet.conn
        conn.send(self.header)
        
        length = self.size
        sended = 0
        buff   = 8192
        while sended < length:
            if length - sended > buff:
                temp = self.f.read(buff)
            else:
                temp = self.f.read(length - sended)
            pros = len(temp)
            sended += pros
            conn.send(temp)
        conet.que.get()
        conet.que.task_done()
    
    def Now_Progress(self, conet, console):
        from rich.console  import Console, Group
        from rich.progress import Progress
        from rich.progress import (
            BarColumn,
            DownloadColumn,
            Progress,
            SpinnerColumn,
            TaskProgressColumn,
            TimeElapsedColumn,
            TimeRemainingColumn,
            TransferSpeedColumn,
        )

        with Progress(
            SpinnerColumn(),
            "{task.description}",
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            resp = {
                'command':'flow_trans',
                'data':self.data
            }
            conet.sendata(resp)
            conet.que.put(RanCode(4))
            conn = conet.conn
            conn.send(self.header)
            
            length = self.size
            task = progress.add_task("[green3]Push", total=length)
            progress.update(task, advance=0)
            sended = 0
            buff   = 8192
            while sended < length:
                if length - sended > buff:
                    temp = self.f.read(buff)
                else:
                    temp = self.f.read(length - sended)
                pros = len(temp)
                sended += pros
                progress.update(task, advance=pros)
                conn.send(temp)
            
            conet.que.get()
            conet.que.task_done()

class RemoteGet:
    def __init__(self, conet:Conet):
        self.conet = conet
        self.conn = self.conet.conn
        self.buff = 8192
    
    def To(self, f):
        self.f = f
        return self

    def Now(self, func=None):
        data = BasicProtocol()
        header = b''
        while len(header) < 10:
            temp = self.conn.recv(1)
            header += temp
            if temp == b'':break
        
        length = ReadHead(header)[3]
        recvdata = 0
        while recvdata < length:
            if length - recvdata > self.buff:
                temp = self.conn.recv(self.buff)
            else:
                temp = self.conn.recv(length - recvdata)
            pros = len(temp)
            recvdata += pros
            self.f.write(temp)
            if temp == b'':break

    def Now_Progress(self, console):
        from rich.console  import Console, Group
        from rich.progress import Progress
        from rich.progress import (
            BarColumn,
            DownloadColumn,
            Progress,
            SpinnerColumn,
            TaskProgressColumn,
            TimeElapsedColumn,
            TimeRemainingColumn,
            TransferSpeedColumn,
        )

        with Progress(
            SpinnerColumn(),
            "{task.description}",
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            data = BasicProtocol()
            header = b''
            while len(header) < 10:
                temp = self.conn.recv(1)
                header += temp
                if temp == b'':break
            
            length = ReadHead(header)[3]
            task = progress.add_task("[green3]Get.", total=length)
            progress.update(task, advance=0)
            recvdata = 0
            while recvdata < length:
                if length - recvdata > self.buff:
                    temp = self.conn.recv(self.buff)
                else:
                    temp = self.conn.recv(length - recvdata)
                pros = len(temp)
                recvdata += pros
                progress.update(task, advance=pros)
                self.f.write(temp)
                if temp == b'':break


class RemoteExtension:
    def __init__(self, node, mac:str):
        self.node = node
        self.now_path = ''
        self.mac  = mac
        self.info = {}
        meth = self.node.server.get('meth', {})
        if not 'activities' in list(meth.keys()):
            raise RemoteConnection('<activities> is not been supported.')
        if not 'multi_cmd' in list(meth.keys()):
            raise RemoteConnection('<multi_cmd> is not been supported.')
        
        for i in self.online():
            if i.get('mac') == self.mac:
                self.info = i
                break
        if self.info == {}:
            raise RemoteConnection('Target {} is not online.'.format(self.mac))
        
        self.node.remote = self.mac
        self.getcwd()

        self.setup()
    
    def setup(self):
        pass

    def send(self, cmd:str, data:dict={}):
        data['remote']  = self.mac
        data['command'] = cmd
        self.node.send('multi_cmd', data)
    
    def online(self):
        self.node.send('activities')
        data = self.node.recv()
        return data
        
    def getcwd(self):
        self.send('pwd')
        resp = self.node.recv(timeout=10)
        path = self.node.recv(timeout=10).get('data', {}).get('resp', '')
        self.now_path = path
        return path