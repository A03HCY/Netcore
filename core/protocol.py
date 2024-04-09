from   secrets import choice
from   string  import ascii_letters, digits
import struct
import ast, json
import queue, threading


def safecode(length:int=4):
    res = ''.join(choice(ascii_letters + digits) for x in range(length))
    return res

def bytes_format(value:int, space:str=' ', point:int=2):
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB']
    size = 1024.0
    for i in range(len(units)):
        if (value / size) < 1:
            return ''.join([str(round(value, point)), space, units[i]])
        value = value / size

def calc_divisional_range(size, chuck=10):
    step = size//chuck
    arr = list(range(0, size, step))
    result = []
    for i in range(len(arr)-1):
        s_pos, e_pos = arr[i], arr[i+1]-1
        result.append([s_pos, e_pos])
    result[-1][-1] = size-1
    return result

def split_bytes_into_chunks(data, chunk_size=2048):
    chunks = []
    num_chunks = (len(data) + chunk_size - 1) // chunk_size
    for i in range(num_chunks):
        start = i * chunk_size
        end = (i + 1) * chunk_size
        chunk = data[start:end]
        chunks.append(chunk)
    return chunks


class Protocol:
    def __init__(self, meta:bytes=b'', extension:str='', encoding:str='utf-8', buff:int=2048) -> None:
        self.buff = buff            # Buffer
        self.meta = bytearray(meta) # Data content
        self.extn = extension       # Label
        self.enco = encoding        # Coding method
        self.leng = 0               # Length of data content, auto-update with function updata()
        self.now  = 0               # Location
        if meta:self.leng = len(meta)
        self.update()
    
    def __str__(self) -> str:
        self.update()
        return 'Extension:{} Length:{:.0f}'.format(self.extn, self.leng)
    
    def update(self):
        # update the head_data
        self.leng = len(self.meta)
        return self

    def upmeta(self, data):
        # reset the meta data
        if type(data) == str:
            self.meta = data.encode(self.enco)
        elif type(data) in [int, float, bytearray, bytes]:
            self.meta = bytes(data)
        else:
            self.meta = str(data).encode(self.enco)
        return self

    @property
    def head(self) -> bytes:
        # return the head data
        self.update()
        head_meta = self.make_head(self.extn, self.leng, self.enco)
        return head_meta

    @property
    def code(self) -> bytes:
        return self.meta.decode(self.enco)
    
    @property
    def json(self) -> dict:
        try:
            data = json.loads(self.code)
            return data
        except: pass
        try:
            data = ast.literal_eval(self.code)
            if type(data) != dict:
                data = {data}
            return data
        except: pass
    
    def pack(self) -> bytes:
        # return the full data
        return self.head + bytes(self.meta)
    
    def unpack(self, data:bytes) -> bool:
        # give a full data then reset self by the result
        self.extn, self.leng, seek = self.parse_static_head(data)
        meta = data[seek:]
        if len(meta) == self.leng:
            self.meta = meta
            return True
        else:
            return False
    
    def write(self, data:bytes):
        if self.now + len(data) < self.leng:
            self.meta[self.now:self.now+len(data)] = data
        else:self.meta[self.now:] = data
        self.now += len(data) - 1
        self.update()
        return self
    
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
    
    def seek(self, location:int):
        if location > self.leng:raise LookupError('Out of writable range')
        self.now = location
        return self
    
    def load_stream(self, func, from_head:tuple=None):
        if not from_head:
            self.extn, self.leng, _ = self.parse_stream_head(func)
        else:
            self.extn, self.leng, _ = from_head
        self.meta = self.stream_until(func, self.leng)
        self.update()
        return self
    
    def create_stream(self, func):
        original_now = self.now
        self.seek(0)
        func(self.head)
        self.stream_until(self.read, self.leng, writefunc=func)
        self.now = original_now
        return self
    
    @staticmethod
    def ignore_stream(func, from_head:tuple) -> None:
        Protocol.stream_until(func, from_head[1], ignore=True)

    @staticmethod
    def save_stream_io(func, file, head:bool=True) -> None:
        meta_head = Protocol.parse_stream_head(func)
        if head:file.write(meta_head[2])
        Protocol.stream_until(func, meta_head[1], writefunc=file.write)
    
    @staticmethod
    def convet_full_stream_io(fromfunc, tofunc) -> None:
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
    def recv_stream_only_by_extn(func, extension:str):
        head = Protocol.parse_stream_head(func)
        if not head[0] == extension:
            Protocol.ignore_stream(func=func, from_head=head)
            return None
        ptcl = Protocol()
        ptcl.load_stream(func=func, from_head=head)
        return ptcl
    

class Bridge:
    def __init__(self, sender, recver, buff:int=2048):
        self.buff   = buff
        self.sender = sender
        self.recver = recver
    
    def protocol_full(self):
        Protocol.convet_full_stream_io(self.recver, self.sender)
    
    def protocol_meta(self):
        meta_head = Protocol.parse_stream_head(self.recver)
        Protocol.stream_until(self.recver, meta_head[1], writefunc=self.sender)

    def data(self):
        while True:
            data = self.recver()
            self.sender(data)


class Pakage:
    def __init__(self, sender, recver, buff:int=2048):
        self.buff   = buff
        self.sender = sender
        self.recver = recver
        self.__isok = False
    
    def start(self):
        self.__isok = True
        self.__send_queue  = queue.Queue()
        self.__recv_queue  = queue.Queue()
        self.__recv_pools  = {}
        self.__send_thread = threading.Thread(target=self.__sender)
        self.__recv_thread = threading.Thread(target=self.__recver)
        self.__send_thread.start()
        self.__recv_thread.start()
        return self
    
    @property
    def is_run(self) -> bool:
        return self.__isok
    
    def close(self):
        self.__isok = False
        return self
    
    def block(self, ifok):
        while not ifok: pass
    
    def send(self, data):
        if not self.__isok: return
        code = safecode()
        if type(data) == Protocol:
            head = Protocol(extension=f'.head_{code}')
            meta = Protocol(extension=f'.meta_{code}_0')
            head.upmeta({
                'head': str(data.extn),
                'type': 'protocol',
                'leng': data.leng,
                'chunks': (len(data.meta) + self.buff - 1) // self.buff
            })
            meta.upmeta(data.meta)
        else:
            meta = Protocol(extension=f'.meta_{code}_0')
            meta.upmeta(bytes(data))
            head = Protocol(extension=f'.head_{code}')
            head.upmeta({
                'type': str(type(data)),
                'leng': len(meta.meta),
                'chunks': (len(meta.meta) + self.buff - 1) // self.buff
            })
        self.__send_queue.put(head)
        self.__send_queue.put(meta)
    
    def recv(self):
        if not self.__isok: return
        result = self.__recv_queue.get(block=True)
        self.__recv_queue.task_done()
        return result
    
    def __sender(self):
        while self.__isok:
            data = self.__send_queue.get()
            if not type(data) == Protocol: continue

            info = str(data.extn).split('_')
            extn = info[0]

            if extn == '.head':
                try:
                    data.create_stream(self.sender)
                except:
                    self.close()
                    break
                continue

            if extn == '.meta':
                current = int(info[2])
                if len(data.meta) - self.buff*current > self.buff:
                    print(current)
                    temp = data.meta[self.buff*(current):self.buff*(current + 1)]
                    Protocol(meta=temp, extension=data.extn, encoding=data.enco, buff=self.buff).create_stream(self.sender)
                    data.extn = '_'.join([info[0], info[1], str(int(info[2]) + 1)])
                    self.__send_queue.put(data)
                else:
                    data.upmeta(data.meta[self.buff*current:]).create_stream(self.sender)
                continue

    def __recver(self):
        while self.__isok:
            data = Protocol().load_stream(self.recver)
            if not type(data) == Protocol: continue

            info = str(data.extn).split('_')
            extn = info[0]
            safe = info[1]

            if info[0] == '.head':
                self.__recv_pools[safe] = {
                    'type': data.json['type'],
                    'head': data.json.get('head'),
                    'leng': data.json['leng'],
                    'chunks': data.json['chunks'],
                    'meta': {}
                }
                for i in range(self.__recv_pools[safe]['chunks']): self.__recv_pools[safe]['meta'][i] = None

            if extn == '.meta':
                current = int(info[2])
                if not safe in self.__recv_pools: continue
                self.__recv_pools[safe]['meta'][current] = data.meta
            
            temp_pop = []
            for safe in self.__recv_pools:
                data = self.__recv_pools[safe]
                if None in data['meta'].values(): continue
                value = b''.join(data['meta'].values())
                if data['type'] == 'protocol':
                    self.__recv_queue.put(Protocol(extension=data['head']).upmeta(value))
                    temp_pop.append(safe)
                    print('recved one')
                else:
                    command = f"{data['transfer']}({value})"
                    try:
                        result = ast.literal_eval(command)
                    except:
                        result = value
                    self.__recv_queue.put(result)
                    temp_pop.append(safe)
                    print('recved one')
            for safe in temp_pop:
                self.__recv_pools.pop(safe)