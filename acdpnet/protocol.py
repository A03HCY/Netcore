from acdpnet import datasets
from secrets import choice
from string  import ascii_letters, digits
from ast     import literal_eval

import struct
import queue
import threading as td



def safecode(length:int=4):
    res = ''.join(choice(ascii_letters + digits) for x in range(length))
    return res


def setio(read, write):
    datasets.set('readio', read)
    datasets.set('writeio', write)


def gobwrite(fromfunc=None):
    if fromfunc: return fromfunc
    if datasets.get('writeio'): return datasets.get('writeio')
    raise ValueError()


def gobread(fromfunc=None):
    if fromfunc: return fromfunc
    if datasets.get('readio'): return datasets.get('readio')
    raise ValueError()


class Protocol:
    def __init__(self, meta:bytes=b'', extension:str='.unknow', encoding:str='utf-8') -> None:
        self.buff = 2048            # Buffer
        self.meta = bytearray(meta) # Data content
        self.extn = extension       # Label
        self.enco = encoding        # Coding method
        self.leng = 0               # Length of data content, auto-update with function updata()
        self.now  = 0               # Location of seeking
        if meta:self.leng = len(meta)
        self.update()
    
    def __str__(self) -> str:
        self.update()
        return 'Type:{} Length:{:.0f}'.format(self.extn, self.leng)
    
    def update(self):
        # update the head_data
        self.leng = len(self.meta)

    def head(self) -> bytes:
        # return the head data
        self.update()
        head_meta = self.make_head(self.extn, self.leng, self.enco)
        return head_meta
    
    def pack(self) -> bytes:
        # return the full data
        return self.head() + bytes(self.meta)
    
    def unpack(self, data:bytes) -> bool:
        # give a full data then reset self by the result
        self.extn, self.leng, seek = self.parse_static_head(data)
        meta = data[seek:]
        if len(meta) == self.leng:
            self.meta = meta
            return True
        else:
            return False
    
    def write(self, data:bytes) -> None:
        if self.now + len(data) < self.leng:
            self.meta[self.now:self.now+len(data)] = data
        else:self.meta[self.now:] = data
        self.now += len(data) - 1
        self.update()
    
    def read(self, length:int=None) -> bytes:
        self.update()
        if not length:length = self.leng - self.now
        try:
            data = self.meta[self.now:self.now+length]
            self.now += length
            return bytes(data)
        except:raise LookupError('Out of readable range')
    
    def readbit(self, buff:int) -> tuple:
        # meta, bool of if is all has been read
        try:
            return self.read(length=buff), False
        except:
            return self.read(), True
    
    def seek(self, location:int) -> None:
        if location > self.leng:raise LookupError('Out of writable range')
        self.now = location
    
    def load_stream(self, func, from_head:tuple=None) -> bool:
        if not from_head:
            self.extn, self.leng, _ = self.parse_stream_head(func)
        else:
            self.extn, self.leng, _ = from_head
        self.meta = self.stream_until(func, self.leng)
        self.update()
        return True
    
    def create_stream(self, func) -> None:
        original_now = self.now
        self.seek(0)
        func(self.head())
        self.stream_until(self.read, self.leng, writefunc=func)
        self.now = original_now
    
    @staticmethod
    def ignore_stream(func, from_head:tuple) -> None:
        Protocol.stream_until(func, from_head[1], ignore=True)

    @staticmethod
    def save_stream_io(func, file, head:bool=True) -> None:
        meta_head = Protocol.parse_stream_head(func)
        if head:file.write(meta_head[2])
        Protocol.stream_until(func, meta_head[1], writefunc=file.write)
    
    @staticmethod
    def convet_full_io_stream(fromfunc, tofunc) -> None:
        meta_head = Protocol.parse_stream_head(fromfunc)
        tofunc(meta_head[2])
        Protocol.stream_until(fromfunc, meta_head[1], writefunc=tofunc)
    
    @staticmethod
    def stream_until(func, length:int, buff:int=2048, writefunc=None, ignore=False) -> bytes:
        data = bytearray(b'')
        seek = 0
        while True:
            if length - seek > buff:
                need = buff
            else:
                need = length - seek
            temp = func(need)
            if writefunc:
                writefunc(temp)
            elif not ignore:
                data += temp
            seek += len(temp)
            if seek >= length:break # DP: '>='
        return bytes(data)
    
    @staticmethod
    def parse_stream_head(func, decoding:str='utf-8') -> tuple:
        meta_code = func(1)
        extn_code = int.from_bytes(meta_code, 'big')
        meta_extn = Protocol.stream_until(func, extn_code)
        extn_meta = meta_extn.decode(decoding)
        meta_leng = func(4)
        leng_code = struct.unpack('i', meta_leng)[0]
        meta_head = meta_code + meta_extn + meta_leng
        return extn_meta, leng_code, meta_head
    
    @staticmethod
    def parse_static_head(data:bytes, decoding:str='utf-8') -> tuple:
        extn_code = data[0] + 1
        extn_meta = data[1:extn_code].decode(decoding)
        seek_to   = extn_code+4
        leng_code = struct.unpack('i', data[extn_code:seek_to])[0]
        return extn_meta, leng_code, seek_to
    
    @staticmethod
    def make_head(extn:str, length:int, encoding:str='utf-8') -> bytes:
        extn_meta = (extn).encode(encoding)
        extn_code = bytes([len(extn_meta)])
        leng_code = struct.pack('i', length)
        head_meta = extn_code + extn_meta + leng_code
        return head_meta
    
    @staticmethod
    def recv_stream_only(func, extension:str):
        head = Protocol.parse_stream_head(func)
        if not head[0] == extension:
            Protocol.ignore_stream(func=func, from_head=head)
            return None
        ptcl = Protocol()
        ptcl.load_stream(func=func, from_head=head)
        return ptcl


def send(data:Protocol):
    if not datasets.get('writeio'): return
    wtio = datasets.get('writeio')
    data.create_stream(wtio)


class Autils:
    @staticmethod
    def chains(extn):
        data = extn[1:].split('.')
        head = data[0]
        extn = '.' + '.'.join(data[1:])
        return head, extn

# Todo Apis:
#   List processing datas in recving or sending
#   then we need a Manager

class Acdpnet:
    def __init__(self):
        self.ok = False
        self.tred = False
        self.temp_rcv = {}
        self.recv_que = queue.Queue()
        self.head_que = queue.Queue()
        self.list_snd = []
        self.pool = {}
        self.recv_func = None
        self.send_func = None
        try:
            self.setio()
        except:pass

    def setio(self, read=None, write=None):
        self.rd = gobread(read)
        self.wt = gobwrite(write)
        self.ok = True
        return self

    def multi_push(self, data:Protocol):
        # add a data to the que
        safe = safecode(4)
        self.pool[safe] = data
        head = self.info(data)
        head.extn += '.' + safe
        self.head_que.put(head)
    
    def singl_push(self, data: Protocol):
        self.list_snd.append(data)

    def multi_send(self):
        while not self.head_que.empty():
            head = self.head_que.get()
            head.create_stream(self.leavin)
        for i in self.pool:
            data = self.pool[i]
            meta, end = data.readbit(2048)
            meta = Protocol(meta=meta, extension='.multi_obj.{}'.format(i))
            meta.create_stream(self.leavin)
            if not end: continue
            del self.pool[i]
    
    def singl_send(self):
        for i in self.list_snd: i.create_stream(self.leavin)
        self.list_snd = []

    def singl_recv(self):
        data = Protocol()
        data.load_stream(self.rd)
        leng = data.leng
        meta = data.meta
        head, extn = Autils.chains(data.extn)
        
        if head == 'multi_head':
            safe, extn = Autils.chains(extn)
            self.temp_rcv[safe] = {
                'head': meta,
                'meta': bytes(),
                'leng': 0
            }
            return
        if head == 'multi_obj':
            safe, extn = Autils.chains(extn)
            self.temp_rcv[safe]['meta'] += meta
            self.temp_rcv[safe]['leng'] += data.leng

            # leng info of head, in order to compa
            _, tlen, _ = Protocol.parse_static_head(self.temp_rcv[safe]['head'])
            if tlen == self.temp_rcv[safe]['leng']:
                data = Protocol()
                data.unpack(
                    self.temp_rcv[safe]['head'] + self.temp_rcv[safe]['meta']
                )
                self.arrivin(data)
                del self.temp_rcv[safe]
            return
        
        self.arrivin(data)
    
    def multi_recv(self):
        self.singl_recv()
        while self.temp_rcv: self.singl_recv()
    
    def arrivin(self, data):
        if not self.recv_func:
            self.recv_que.put(data)
            return
        unsave = self.recv_func(data)
        if unsave in [None, False]: self.recv_que.put(data)
    
    def leavin(self, meta):
        if self.send_func: self.send_func(meta)
        self.wt(meta)
    
    # Threading
    def recv_start(self, wait:bool=False):
        if self.tred: return
        self.tred = True
        self.thread = td.Thread(target=self.recv_thread_func)
        self.thread.start()
        if wait: self.thread.join()
    
    def recv_join(self):
        if not self.tred: return
        if self.thread: self.thread.join()

    def recv_thread_func(self):
        try:
            while True: self.singl_recv()
        except:
            print('Connection closed')
            self.tred = False
    
    @staticmethod
    def info(data:Protocol):
        info = Protocol(data.head(), extension='.multi_head')
        return info


class Netgroup:
    def __init__(self):
        self.pool = {}
    
    def add(self, net:Acdpnet, name:str):
        self.pool[name] = net
    
    def net(self, name:str) -> Acdpnet:
        return self.pool.get(name)
    
    def new(self, name:str, read, write) -> Acdpnet:
        self.pool[name] = Acdpnet().setio(read=read, write=write)
        return self.pool[name]
    
    def remove(self, name:str):
        pass

    def destroy(self, name:str):
        pass


'''
.multi-{}.{safecode}.extn.args
.extn.args
'''
