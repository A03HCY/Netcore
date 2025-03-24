from typing import Callable, Union, Optional, Generator, Tuple
from struct import pack, unpack
from os     import path, read as osread
from mmap   import mmap, ACCESS_WRITE
from random import choices
from string import ascii_letters, digits

from queue     import Queue
from threading import Thread
import json
import logging

# 配置日志记录器
logger = logging.getLogger("netcore.lso")

class Utils:
    """工具类，提供各种实用的静态方法。
    
    此类包含多种帮助函数，用于格式化数据、分割数据块、生成安全码等操作。
    所有方法都是静态的，可以直接通过类名调用。
    """
    
    @staticmethod
    def bytes_format(value:int, space:str=' ', point:int=2) -> str:
        """将字节大小格式化为人类可读的字符串。
        
        Args:
            value: 字节数量
            space: 数字和单位之间的分隔符，默认为空格
            point: 小数点后保留的位数，默认为2
            
        Returns:
            str: 格式化后的字符串，如 "1.25 KB"
            
        Examples:
            >>> Utils.bytes_format(1500)
            '1.46 KB'
        """
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB']
        size = 1024.0
        for i in range(len(units)):
            if (value / size) < 1:
                return ''.join([str(round(value, point)), space, units[i]])
            value = value / size
    
    @staticmethod
    def calc_divisional_range(size, chuck=10) -> list:
        """将指定大小分割成多个范围块。
        
        Args:
            size: 总大小
            chuck: 分割的块数，默认为10
            
        Returns:
            list: 包含多个 [起始位置, 结束位置] 的列表
            
        Examples:
            >>> Utils.calc_divisional_range(100, 4)
            [[0, 24], [25, 49], [50, 74], [75, 99]]
        """
        step = size//chuck
        arr = list(range(0, size, step))
        result = []
        for i in range(len(arr)-1):
            s_pos, e_pos = arr[i], arr[i+1]-1
            result.append([s_pos, e_pos])
        result[-1][-1] = size-1
        return result
    
    @staticmethod
    def split_bytes_into_chunks(data, chunk_size=4096) -> list:
        """将字节数据分割成固定大小的块。
        
        Args:
            data: 要分割的字节数据
            chunk_size: 每个块的大小，默认为4096字节
            
        Returns:
            list: 包含分割后的数据块的列表
            
        Examples:
            >>> data = b'hello world' * 1000
            >>> chunks = Utils.split_bytes_into_chunks(data, 1000)
            >>> len(chunks)
            11
        """
        chunks = []
        num_chunks = (len(data) + chunk_size - 1) // chunk_size
        for i in range(num_chunks):
            start = i * chunk_size
            end = (i + 1) * chunk_size
            chunk = data[start:end]
            chunks.append(chunk)
        return chunks
    
    @staticmethod
    def safe_code(length:int) -> str:
        """生成指定长度的随机安全码。
        
        使用字母和数字的组合生成随机字符串，可用于各种需要唯一标识符的场景。
        
        Args:
            length: 要生成的安全码长度
            
        Returns:
            str: 随机安全码
            
        Examples:
            >>> Utils.safe_code(8)  # 返回类似 'a2Bc7dEf' 的8字符随机码
        """
        return ''.join(choices(ascii_letters + digits, k=length))


'''
LsoPrococol:
extension_length(struct, length=4) | extension(bytes) | meta_length(struct, length=4) | meta(bytes)
'''

class LsoProtocol:
    def __init__(self, local: Optional[str]=None, encoding:str='utf-8', buff: int = 2048):
        """
        初始化 LsoProtocol 实例。

        Args:
            local (Optional[str]): 本地文件路径，若为 None 则不使用本地存储。
            encoding (str): 字符编码，默认为 'utf-8'。
            buff (int): 缓冲区大小，默认为 2048 字节。
        """
        self._meta = bytearray()
        self.encoding = encoding
        self.local = local if isinstance(local, str) else None
        self.buff = buff
        self._extension = b''
        self.exp_data = {}
        # check file
        if self.local:
            self.verify(self.local, recreate=True)
            with open(self.local, 'rb') as f:
                extn_length = unpack('i', f.read(4))[0]
                self._extension = f.read(extn_length)
    
    def __str__(self):
        return self._extension
    
    @property
    def length(self) -> int:
        """
        获取当前存储的元数据长度。

        Returns:
            int: 元数据的字节长度。
        """
        if self.local:
            return path.getsize(self.local) - len(self._extension) - 8
        return len(self._meta)
    
    @property
    def meta(self) -> bytes:
        return self._meta
    
    @property
    def json(self) -> dict:
        try:
            return json.loads(self._meta)
        except:
            return {}
    
    @property
    def extension(self) -> str|bytes:
        """
        获取当前扩展名。

        Returns:
            str: 扩展名的字符串。
        """
        if isinstance(self._extension, bytes):
            return self._extension.decode(encoding=self.encoding)
        return self._extension
    
    @extension.setter
    def extension(self, value: Union[bytes, str]) -> None:
        """
        设置对象的扩展名属性。

        此方法用于更新对象的扩展名，支持字节和字符串类型的输入。
        如果输入值是字节类型，则直接赋值给内部变量；
        如果是字符串类型，则使用对象的编码方式将其转换为字节后赋值；
        对于其他类型，尝试将其转换为字节，转换失败则抛出 ValueError 异常。

        若对象处于本地模式，还会进行一系列操作：
        1. 验证本地文件并重新创建（如果必要）。
        2. 使用内存映射（mmap）来更新本地文件中的扩展名部分。
            - 计算新旧扩展名的长度差异。
            - 根据差异调整内存映射的大小，并移动数据以腾出空间或填补空缺。
            - 写入新的扩展名长度和扩展名数据。
            - 刷新内存映射并关闭。

        如果在更新过程中发生任何异常，将抛出一个包含错误信息的 Exception 异常。

        Args:
            value (Union[bytes, str]): 新的扩展名，可以是字节或字符串。

        Raises:
            ValueError: 如果值的类型不是 'bytes' 或 'str'。
            Exception: 如果在更新扩展名过程中发生错误。
        """
        if isinstance(value, bytes):
            self._extension = value
        elif isinstance(value, str):
            self._extension = value.encode(self.encoding)
        else:
            try: self._extension = bytes(value)
            except: raise ValueError("extension must be of type 'bytes' or 'str'")
        if not self.local: return
        self.verify(self.local, recreate=True)
        try:
            new_extn_length = len(self._extension) + 4
            mm = None
            # 使用 mmap 更新本地文件
            with open(self.local, 'r+b') as f:
                mm = mmap(f.fileno(), 0, access=ACCESS_WRITE)
                old_extn_length = unpack('i', mm[:4])[0] + 4
                diff = new_extn_length - old_extn_length
                if diff > 0:
                    mm.resize(mm.size() + diff)
                    mm.move(new_extn_length, old_extn_length, len(mm[old_extn_length:]) - diff)
                else:
                    mm.move(new_extn_length, old_extn_length, len(mm[old_extn_length:]))
                mm.seek(0)
                mm.write(pack('i', len(self._extension)))
                mm.write(self._extension)
                if diff < 0:
                    mm.resize(mm.size() + diff)
                mm.flush()
        except Exception as e:
            raise Exception(f"Error updating extension: {e}")
        finally:
            if mm: mm.close()
    
    @property
    def head(self) -> bytes:
        """
        生成并返回数据头部。

        Returns:
            bytes: 包含扩展名和元数据长度的字节序列。
        """
        # code self._extension
        head = self._extension
        head = pack('i', len(head)) + head
        # code self._meta
        head += pack('i', len(self._meta))
        return head

    @staticmethod
    def verify(local:str, recreate:bool=False) -> bool:
        """
        验证本地文件头部信息的有效性。
        
        不对长度是否符合头部信息进行验证。

        Args:
            local (str): 文件路径。
            recreate (bool): 如果文件无效，是否重新创建文件。

        Returns:
            bool: 如果文件有效返回 True，否则返回 False。
        """
        if not path.exists(local):
            if recreate: LsoProtocol.create_empty_file(local, '')
            return False
        if path.getsize(local) < 8:
            if recreate: LsoProtocol.create_empty_file(local, '')
            return False
        try:
            with open(local, 'rb') as f:
                extn_length = unpack('i', f.read(4))[0]
                extension = f.read(extn_length)
        except:
            if recreate: LsoProtocol.create_empty_file(local, '')
            return False
        return True
    
    @staticmethod
    def check_complete(local:str) -> Tuple[bool, int]:
        """
        检查指定文件中是否缺失元数据，并返回缺失情况。

        验证文件的有效性，如果文件无效则抛出 FileExistsError。
        读取文件中的扩展名和元数据长度，并计算实际数据大小与元数据长度之间的差异。

        Args:
            local (str): 要检查的文件路径。

        Returns:
            Tuple[bool, int]: 
                - bool: 如果缺失的大小为 0，返回 True；否则返回 False。
                - int: 缺失的字节数。
        
        Raises:
            FileNotFoundError: 如果文件无效。
        """
        if not LsoProtocol.verify(local): raise FileNotFoundError()
        with open(local, 'rb') as f:
            extn_length = unpack('i', f.read(4))[0]
            extension = f.read(extn_length)
            head_length = extn_length + 8
            meta_length = unpack('i', f.read(4))[0]
            size = path.getsize(local) - head_length
            missing = size - meta_length
        return missing == 0, missing
    
    @staticmethod
    def create_empty_file(local:str, extension:Union[str, bytes], encoding:str='utf-8') -> None:
        """
        创建一个空文件并写入扩展名和元数据长度。

        Args:
            local (str): 文件路径。
            extension (Union[str, bytes]): 扩展名，可以是字符串或字节。
            encoding (str): 编码格式，默认为 'utf-8'。
        """
        if isinstance(extension, str): extension = extension.encode(encoding=encoding)
        with open(local, 'wb') as f:
            f.write(pack('i', len(extension)))
            f.write(extension)
            f.write(pack('i', 0))
        return

    @staticmethod
    def function_recv(
            function: Callable[[Optional[int]], Union[bytes, bytearray]], # Data recv function
            length: int,                                                  # Length
            handler: Optional[Union[Callable[[bytes], None], list[Callable[[bytes], None]]]] = None,                  # Handle function
            buff: int = 2048                                              # Buff length
        ) -> bytes:
        """
        从函数中接收指定长度的数据。

        Args:
            function (Callable): 数据接收函数。
            length (int): 期望接收的数据长度。
            handler (Optional[Callable]): 可选的数据处理函数。
            buff (int): 每次读取的字节数。

        Returns:
            bytes: 接收到的字节数据。
        """
        meta = b''
        temp = b''
        is_finished = False
        while not is_finished:
            if len(meta) + buff <= length:
                temp = function(buff)
            else:
                temp = function(length - len(temp))
            meta += temp
            if callable(handler): handler(temp)
            if isinstance(handler, list):
                for i in handler:
                    if callable(i): i(temp)
            if len(meta) == length:
                is_finished = True
        return temp
    
    def _add_meta(self, data:bytes) -> None:
        """
        将元数据添加到本地文件或内存中。

        Args:
            data (bytes): 要添加的字节数据。
        """
        if self.local:
            with open(self.local, 'a+b') as f: f.write(data)
        else:
            self._meta.extend(data)
    
    def _set_length(self, meta_length:int) -> None:
        """
        更新本地文件中的元数据长度。

        Args:
            meta_length (int): 新的元数据长度。
        """
        if not self.local: return
        self.extension = self._extension
        with open(self.local, 'a+b') as f:
            mm = mmap(f.fileno(), 0, access=ACCESS_WRITE)
            mm.seek(len(self._extension) + 4)
            mm.write(pack('i', meta_length))
            mm.flush()
    
    def set_meta(self, data:Union[bytes, bytearray, str]) -> None:
        """
        设置元数据。

        Args:
            data (Union[bytes, bytearray, str]): 要设置的元数据，可以是字节、字节数组或字符串。

        Raises:
            ValueError: 如果数据类型不正确。
        """
        if   isinstance(data, bytes): data = bytearray(data)
        elif isinstance(data, bytearray): pass
        elif isinstance(data, str): data = bytearray(data, encoding=self.encoding)
        else: raise ValueError('Invalid data type for meta.')
        if not self.local:
            self._meta = data
            return
        start = len(self._extension) + 4
        with open(self.local, 'a+b') as f:
            mm = mmap(f.fileno(), 0, access=ACCESS_WRITE)
            mm.resize(start + len(data) + 4)
            mm.seek(start)
            mm.write(pack('i', len(data)))
            mm.write(data)

    def full_data(self, buff:Optional[int] = None) -> Generator:
        """
        生成器，逐块返回完整数据。

        Args:
            buff (Optional[int]): 每次读取的字节数，默认为实例的 buff 属性。

        Yields:
            bytes: 返回读取的数据块。
        """
        if not buff: buff = self.buff
        # 如果有本地文件，读取文件内容
        if self.local:
            with open(self.local, 'rb') as f:
                while True:
                    data = osread(f.fileno(), buff)
                    if not data:
                        break
                    yield data
        else:
            yield self.head
            # 否则直接返回存储在 _meta 中的数据
            for i in range(0, len(self._meta), buff):
                data = self._meta[i:i + buff]
                yield data if isinstance(data, bytearray) else bytearray(bytes(data, encoding=self.encoding))
    
    def load_stream(
        self, 
        function: Callable[[Optional[int]], Union[bytes, bytearray]], 
        head: Optional[Union[bytes, bytearray]] = None,
        handler: Optional[Callable[[bytes], None]] = None,
        buff: Optional[int] = None
    ) -> 'LsoProtocol':
        """
        从流中加载数据。
    
        Args:
            function (Callable): 数据接收函数，用于从流中读取数据。
            head (Optional[Union[bytes, bytearray]]): 可选的头部数据，如果提供则从头部获取扩展名和元数据长度。
            handler (Optional[Callable]): 可选的数据处理函数，用于处理接收到的数据。
            buff (Optional[int]): 每次读取的字节数，默认为实例的 buff 属性。
    
        Returns:
            self: 当前实例，以便支持链式调用。
        
        Notes:
            - 如果提供了头部数据，则从头部解析扩展名和元数据长度，并将头部数据添加到元数据中。
            - 如果未提供头部数据，则从流中接收头部信息，解析扩展名和元数据长度。
            - 接收所有元数据，并将其添加到实例的元数据中。
            - 如果实例有本地文件路径，则清空该文件；否则，重置实例的元数据。
        """
        if not buff: 
            buff = self.buff
            
        # 清空文件
        if self.local:
            with open(self.local, 'w', encoding=self.encoding) as f: 
                f.write('')
        else: 
            self._meta = bytearray()
            
        # 处理头部信息
        if head:
            # 从头部获取扩展名长度
            extension_length = unpack('i', head[:4])[0]  # 读取扩展名长度
            extension = head[4:4 + extension_length].decode(self.encoding)  # 读取扩展名
            meta_length = unpack('i', head[4 + extension_length:8 + extension_length])[0]  # 读取元数据长度
            if self.local:
                self._add_meta(head)  # 将头部数据添加到元数据中
        else:
            # 从流中接收头部信息
            if self.local:
                extension_length = unpack('i', self.function_recv(function=function, length=4, handler=self._add_meta, buff=buff))[0]
                extension = self.function_recv(function=function, length=extension_length, handler=self._add_meta, buff=buff).decode(self.encoding)
                meta_length = unpack('i', self.function_recv(function=function, length=4, handler=self._add_meta, buff=buff))[0]
            else:
                extension_length = unpack('i', self.function_recv(function=function, length=4, buff=buff))[0]
                extension = self.function_recv(function=function, length=extension_length, buff=buff).decode(self.encoding)
                meta_length = unpack('i', self.function_recv(function=function, length=4, buff=buff))[0]
            
        # 接收所有元数据
        self._extension = extension
        self.function_recv(function=function, length=meta_length, handler=[self._add_meta, handler], buff=buff)
        
        return self
    
    def load_generator(self, generator: Generator, extention:Optional[str]=None, handler:Optional[Callable[[bytes], None]]=None, set_length:bool=True) -> 'LsoProtocol':
        """
	    从数据生成器加载数据并设置扩展名。
        
	    Args:
	        generator (Generator): 数据生成器，生成要加载的数据块。
	        extension (Optional[str]): 可选的扩展名，如果提供，将设置为当前实例的扩展名。
	        handler (Optional[Callable]): 可选的数据处理函数，在每次接收数据时调用。
	        set_length (bool): 是否在加载完成后更新元数据长度，默认为 True。
            
	    Returns:
	        self: 当前实例，便于链式调用。
            
	    Notes:
	        - 如果实例使用本地文件存储，将首先清空文件内容。
	        - 在加载数据时，所有接收到的数据将被添加到元数据中。
	        - 如果提供了扩展名，将在加载数据之前设置它。
	        - 每次接收数据时，如果提供了处理函数，将会被调用。
        """
        # 清空文件
        if self.local:
            with open(self.local, 'w', encoding=self.encoding) as f: 
                f.write('')
        else: 
            self._meta = bytearray()
        if extention:
            self.extension = extention
        length = 0
        if set_length: self._set_length(length)
        for data in generator:
            if not data: continue
            if callable(handler): handler(data)
            length += len(data)
            self._add_meta(data)
        if set_length: self._set_length(length)
        return self
    
    def release_headinfo(self) -> None:
        """
        释放头部信息，如果文件存在并有效，则调整文件内容。

        如果本地文件存在且有效，移除文件头部信息，并更新文件大小。

        Returns:
            None
        """
        if not self.local or not self.verify(self.local): return
        with open(self.local, 'r+b') as f:
            mm = mmap(f.fileno(), 0, access=ACCESS_WRITE)
            size = mm.size()
            head_length = len(self._extension) + 8
            mm.move(0, head_length, size - head_length)
            mm.resize(size - head_length)
            mm.flush()
        self.local = None
    
    def save(self, path:str):
        """
        将数据保存到指定路径。

        Args:
            path (str): 保存文件的路径。
        """
        if self.local: return
        with open(path, 'wb') as f:
            for data in self.full_data():
                f.write(data)
        self.local = path
    
    def reveal_private(self, function_name:str) -> Callable:
        """
        根据给定的函数名揭示对应的私有方法。
    
        Args:
            function_name (str): 要揭示的私有方法的名称。
    
        Returns:
            Callable: 对应的私有方法。
    
        Notes:
            此方法用于在特定情况下访问类的私有方法，通常不建议在类的外部使用。
        """
        if function_name == 'set_length':
            return self._set_length


'''
Mission Head (use LsoProtocol):
extension: dict {type:mssion} | meta: dict

Mission Data (use LsoProtocol):
extension: str safe_code(6)   | meta: bytes
'''

class Pipe:
    """数据传输管道，用于在不同端点之间传输数据。
    
    此类管理数据的发送和接收，支持任务队列和池，使用线程处理异步操作。
    它是网络通信的核心组件，处理所有数据传输和消息分发。
    """
    
    def __init__(self, recv_function:Callable[[Optional[int]], bytes], send_function:Callable[[bytes], None]):
        """初始化Pipe实例。
        
        Args:
            recv_function: 接收数据的函数，接受一个可选的整数参数（读取的字节数）
            send_function: 发送数据的函数，接受一个字节参数（要发送的数据）
        """
        self.recv_function = recv_function  # 接收数据的函数
        self.send_function = send_function  # 发送数据的函数
        # 任务头队列，优先发送
        self.mission_head = Queue()
        # 任务队列
        self.send_pool: dict[str, Queue|Generator] = {}  # 存储待发送的数据
        # 接收的数据
        self.recv_pool: dict[str, bytes] = {}  # 存储接收到的完整数据
        # 接收的数据的额外信息
        self.recv_info: dict[str, dict] = {}  # 存储接收数据的元信息
        # 临时，在接收完成后转移到 recv_info
        self.temp_pool: dict[str, dict] = {}  # 临时存储接收中的数据
        # 发送任务的额外信息
        self.misson_info: dict[str, dict] = {}  # 存储发送任务的元信息

        # 接收和发送线程
        self.recv_thread = Thread(target=self._recv_thread)
        self.send_thread = Thread(target=self._send_thread)

        # 接收线程是否出错
        self.recv_exception = False
    
    def _recv(self) -> tuple[LsoProtocol, dict]:
        """接收一个完整的LSO协议数据包。
        
        Returns:
            tuple: (LsoProtocol实例, 信息字典)
        """
        lso = LsoProtocol().load_stream(self.recv_function)
        info = json.loads(lso.extension)
        return lso, info
    
    def _send(self, data:bytes, info:dict) -> None:
        """发送数据和相关信息。
        
        Args:
            data: 要发送的字节数据
            info: 与数据相关的元信息
        """
        lso = LsoProtocol(local=None, encoding='utf-8', buff=2048)
        lso.extension = json.dumps(info)
        lso.set_meta(data)
        for i in lso.full_data():
            self.send_function(i)
    
    def create_mission(self, data:bytes, info:dict={}, extension:Optional[str]=None, buff:int=4096) -> str:
        """创建一个发送任务。
        
        将大数据分块并加入发送队列，每块将被单独发送。
        
        Args:
            data: 要发送的字节数据
            info: 与数据相关的元信息
            extension: 可选的扩展标识符，默认生成随机安全码
            buff: 每块数据的大小，默认为4096字节
            
        Returns:
            str: 任务的扩展标识符
        """
        extension = extension or Utils.safe_code(6)
        queue = Queue()
        for i in Utils.split_bytes_into_chunks(data, buff):
            queue.put(i)
        self.send_pool[extension] = queue
        self.misson_info[extension] = {
            'length': len(data)
        }
        # 保存任务到待发送队列
        self.mission_head.put({
            'extension': extension,
            'length': len(data),
            'info': info,
        })
        return extension
    
    def _send_thread(self):
        """发送线程的主函数。
        
        持续监控任务队列并发送数据，处理任务头和任务数据。
        """
        try:
            while True:
                # 接收线程错误时，停止发送线程
                if self.recv_exception:
                    self.recv_exception = False
                    self._send_error_handler('with_exception')
                send_pool_copy = list(self.send_pool.items())
                for extension, queue in send_pool_copy:
                    # 发送任务头
                    while not self.mission_head.empty():
                        mission = self.mission_head.get()
                        self._send(json.dumps(mission), {
                            'type': 'mission'
                        })
                        self.mission_head.task_done()
                    info = self.misson_info[extension]
                    # 发送任务数据
                    if queue.empty():
                        logger.info(f'{extension} mission completed. size: {info["length"]}')
                        self.send_pool.pop(extension)
                        self.misson_info.pop(extension)
                        continue
                    data = queue.get()
                    self._send(data, {
                        'type': 'data',
                        'extension': extension,
                    })
                    queue.task_done()
        except KeyboardInterrupt:
            self._send_error_handler('close')
        except Exception as e:
            self._send_error_handler('error', e)
    
    def _recv_thread(self):
        """接收线程的主函数。
        
        持续接收数据，处理任务头和任务数据，组装完整消息。
        """
        try:
            while True:
                lso, info = self._recv()
                if info['type'] == 'mission':
                    # 接收任务头
                    data = lso.json
                    self.temp_pool[data['extension']] = {
                        'length': data['length'],
                        'recv': 0,
                        'data': bytearray(),
                    }
                    self.recv_info[data['extension']] = data['info']
                    continue
                # 接收任务数据
                self.temp_pool[info['extension']]['data'] += lso.meta
                self.temp_pool[info['extension']]['recv'] += len(lso.meta)
                # 接收任务完成
                if self.temp_pool[info['extension']]['recv'] == self.temp_pool[info['extension']]['length']:
                    self.recv_pool[info['extension']] = self.temp_pool[info['extension']]['data']
                    self.temp_pool.pop(info['extension'])
                    continue
                # 接收任务数据错误
                if self.temp_pool[info['extension']]['recv'] > self.temp_pool[info['extension']]['length']:
                    raise ValueError(f'{info["extension"]} recv length error.')
        except KeyboardInterrupt:
            self._recv_error_handler('close')
        except Exception as e:
            self.recv_exception = True
            self._recv_error_handler('error', e)
    
    def _send_error_handler(self, message:str, exception:Exception=None):
        """处理发送过程中的错误。
        
        Args:
            message: 错误消息类型
            exception: 可选的异常对象
        """
        if message == 'error':
            logger.error(f'Pipe error: {exception}')
        if message == 'close':
            logger.info('Pipe closed.')
        if message == 'with_exception':
            logger.warning('Pipe closed with recv exception.')

    def _recv_error_handler(self, message:str, exception:Exception=None):
        """处理接收过程中的错误。
        
        Args:
            message: 错误消息类型
            exception: 可选的异常对象
        """
        if message == 'error':
            logger.error(f'Pipe error: {exception}')
        if message == 'close':
            logger.info('Pipe closed.')
    
    def send(self, data:bytes, info:dict={}):
        """发送数据和相关信息。
        
        是create_mission的简化版本，用于快速发送数据。
        
        Args:
            data: 要发送的字节数据
            info: 与数据相关的元信息
        """
        self.create_mission(data, info)
    
    def recv(self) -> tuple[bytes, dict]:
        """接收数据和相关信息。
        
        从接收池中获取一个完整的数据包。
        """
        if not self.recv_pool: return None
        extension, data = self.recv_pool.popitem()
        info = self.recv_info.pop(extension)
        info.update({
            'extension': extension
        })
        return data, info
    
    @property
    def is_data(self) -> bool:
        return self.recv_pool != {}
    
    def start(self):
        self.recv_thread.start()
        self.send_thread.start()
