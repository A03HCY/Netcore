from typing    import Callable, Union, Optional, Generator, Tuple
from struct    import pack, unpack
from os        import path, read as osread
from mmap      import mmap, ACCESS_WRITE
from random    import choices
from string    import ascii_letters, digits
from queue     import Queue
from threading import Thread, RLock

import json
import logging

# 配置日志记录器
logger = logging.getLogger("netcore.lso")

class Utils:
    """Utility class providing various static methods.
    
    This class contains helper functions for formatting data, splitting data blocks,
    generating secure codes, and other operations.
    All methods are static and can be called directly through the class name.
    """
    
    @staticmethod
    def bytes_format(value:int, space:str=' ', point:int=2) -> str:
        """Format byte size to human-readable string.
        
        Args:
            value: Number of bytes
            space: Separator between number and unit, default is space
            point: Number of decimal places to keep, default is 2
            
        Returns:
            str: Formatted string, such as "1.25 KB"
            
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
        """Split a given size into multiple range blocks.
        
        Args:
            size: Total size
            chuck: Number of blocks to split into, default is 10
            
        Returns:
            list: List containing multiple [start_pos, end_pos] ranges
            
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
        """Split byte data into fixed-size chunks.
        
        Args:
            data: Byte data to split
            chunk_size: Size of each chunk, default is 4096 bytes
            
        Returns:
            list: List containing split data chunks
            
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
        """Generate a random secure code of specified length.
        
        Uses a combination of letters and digits to generate a random string,
        useful for various scenarios requiring unique identifiers.
        
        Args:
            length: Length of the secure code to generate
            
        Returns:
            str: Random secure code
            
        Examples:
            >>> Utils.safe_code(8)  # Returns an 8-character random code like 'a2Bc7dEf'
        """
        return ''.join(choices(ascii_letters + digits, k=length))


'''
LsoPrococol:
extension_length(struct, length=4) | extension(bytes) | meta_length(struct, length=4) | meta(bytes)
'''

class LsoProtocol:
    """Protocol class for lightweight structured object serialization and deserialization.
    
    Provides methods for handling binary data with extension metadata, useful for
    network communication and file operations.
    """
    
    def __init__(self, local: Optional[str]=None, encoding:str='utf-8', buff: int = 2048):
        """Initialize an LsoProtocol instance.

        Args:
            local: Optional local file path, if None local storage is not used
            encoding: Character encoding, default is 'utf-8'
            buff: Buffer size, default is 2048 bytes
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
        """Get the length of currently stored metadata.

        Returns:
            int: Length of metadata in bytes
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
        """Get the current extension.

        Returns:
            str|bytes: The extension as string or bytes
        """
        if isinstance(self._extension, bytes):
            return self._extension.decode(encoding=self.encoding)
        return self._extension
    
    @extension.setter
    def extension(self, value: Union[bytes, str]) -> None:
        """Set the object's extension attribute.

        This method updates the object's extension, supporting both byte and string inputs.
        If the input is bytes, it's directly assigned to the internal variable;
        If it's a string, it's converted to bytes using the object's encoding;
        For other types, it tries to convert to bytes, raising a ValueError if conversion fails.

        When the object is in local mode, it also performs a series of operations:
        1. Verifies the local file and recreates it if necessary.
        2. Uses memory mapping (mmap) to update the extension part in the local file.
           - Calculates the length difference between new and old extensions.
           - Adjusts the memory map size and moves data to make space or fill gaps.
           - Writes the new extension length and extension data.
           - Flushes and closes the memory map.

        If any exception occurs during the update, an Exception with an error message is raised.

        Args:
            value: New extension, can be bytes or string

        Raises:
            ValueError: If the value type is not 'bytes' or 'str'
            Exception: If an error occurs during extension update
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
        """Generate and return the data header.

        Returns:
            bytes: Byte sequence containing extension and metadata length
        """
        # code self._extension
        head = self._extension
        head = pack('i', len(head)) + head
        # code self._meta
        head += pack('i', len(self._meta))
        return head

    @staticmethod
    def verify(local:str, recreate:bool=False) -> bool:
        """Verify the validity of local file header information.
        
        Does not verify if the length matches the header information.

        Args:
            local: File path
            recreate: If the file is invalid, whether to recreate it

        Returns:
            bool: True if the file is valid, otherwise False
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
        """Check if metadata is missing in the specified file and return the missing status.

        Verifies the validity of the file, raises FileNotFoundError if invalid.
        Reads the extension and metadata length from the file and calculates the difference
        between actual data size and metadata length.

        Args:
            local: Path of the file to check

        Returns:
            Tuple[bool, int]: 
                - bool: True if the missing size is 0, otherwise False
                - int: Number of missing bytes
        
        Raises:
            FileNotFoundError: If the file is invalid
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
        """Create an empty file and write extension and metadata length.

        Args:
            local: File path
            extension: Extension, can be string or bytes
            encoding: Encoding format, default is 'utf-8'
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
        """Receive data of specified length from a function.

        Args:
            function: Data receive function
            length: Expected data length
            handler: Optional data handler function
            buff: Number of bytes to read each time

        Returns:
            bytes: Received byte data
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
        """Add metadata to local file or memory.

        Args:
            data: Byte data to add
        """
        if self.local:
            with open(self.local, 'a+b') as f: f.write(data)
        else:
            self._meta.extend(data)
    
    def _set_length(self, meta_length:int) -> None:
        """Update metadata length in local file.

        Args:
            meta_length: New metadata length
        """
        if not self.local: return
        self.extension = self._extension
        with open(self.local, 'a+b') as f:
            mm = mmap(f.fileno(), 0, access=ACCESS_WRITE)
            mm.seek(len(self._extension) + 4)
            mm.write(pack('i', meta_length))
            mm.flush()
    
    def set_meta(self, data:Union[bytes, bytearray, str]) -> None:
        """Set metadata.

        Args:
            data: Metadata to set, can be bytes, bytearray, or string

        Raises:
            ValueError: If data type is incorrect
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
        """Generator that returns complete data in chunks.

        Args:
            buff: Number of bytes to read each time, defaults to instance's buff attribute

        Yields:
            bytes: Returns the read data chunk
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
        """Load data from a stream.
    
        Args:
            function: Data receive function, used to read data from the stream
            head: Optional head data, if provided extension and metadata length are obtained from it
            handler: Optional data handler function, used to process received data
            buff: Number of bytes to read each time, defaults to instance's buff attribute
    
        Returns:
            self: Current instance, to support chain calling
        
        Notes:
            - If head data is provided, extension and metadata length are parsed from it,
              and the head data is added to metadata.
            - If head data is not provided, head information is received from the stream,
              and extension and metadata length are parsed.
            - All metadata is received and added to the instance's metadata.
            - If the instance has a local file path, that file is emptied; otherwise,
              the instance's metadata is reset.
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
        """Load data from a data generator and set extension.
        
        Args:
            generator: Data generator that produces data chunks to load
            extension: Optional extension, if provided it will be set as the current instance's extension
            handler: Optional data handler function, called each time data is received
            set_length: Whether to update metadata length after loading is complete, default is True
            
        Returns:
            self: Current instance, for chain calling
            
        Notes:
            - If the instance uses local file storage, the file content will be cleared first.
            - During data loading, all received data will be added to metadata.
            - If an extension is provided, it will be set before loading data.
            - Each time data is received, if a handler function is provided, it will be called.
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
        """Release header information, if file exists and is valid, adjust file content.

        If the local file exists and is valid, removes the file header information
        and updates the file size.

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
        """Save data to the specified path.

        Args:
            path: Path to save the file
        """
        if self.local: return
        with open(path, 'wb') as f:
            for data in self.full_data():
                f.write(data)
        self.local = path
    
    def reveal_private(self, function_name:str) -> Callable:
        """Reveal a private method based on the given function name.
    
        Args:
            function_name: Name of the private method to reveal
    
        Returns:
            Callable: The corresponding private method
    
        Notes:
            This method is used to access the class's private methods in specific cases,
            generally not recommended for use outside the class.
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
    """Data transmission pipe for transferring data between different endpoints.
    
    This class manages the sending and receiving of data, supports task queues and pools,
    and uses threads to handle asynchronous operations.
    It is the core component of network communication, handling all data transfer and message distribution.
    """
    
    def __init__(self, recv_function:Callable[[Optional[int]], bytes], send_function:Callable[[bytes], None]):
        """Initialize a Pipe instance.
        
        Args:
            recv_function: Function to receive data, accepts an optional integer parameter (number of bytes to read)
            send_function: Function to send data, accepts a bytes parameter (data to send)
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

        # 添加线程锁
        self.send_lock = RLock()
        self.recv_lock = RLock()

        # 接收和发送线程
        self.recv_thread = Thread(target=self._recv_thread)
        self.send_thread = Thread(target=self._send_thread)

        # 接收线程是否出错
        self.recv_exception = False

        self.final_error_handler: Callable = None
    
    def _recv(self) -> tuple[LsoProtocol, dict]:
        """Receive a complete LSO protocol data packet.
        
        Returns:
            tuple: (LsoProtocol instance, information dictionary)
        """
        lso = LsoProtocol().load_stream(self.recv_function)
        info = json.loads(lso.extension)
        return lso, info
    
    def _send(self, data:bytes, info:dict) -> None:
        """Send data and related information.
        
        Args:
            data: Byte data to send
            info: Metadata related to the data
        """
        lso = LsoProtocol(local=None, encoding='utf-8', buff=2048)
        lso.extension = json.dumps(info)
        lso.set_meta(data)
        for i in lso.full_data():
            self.send_function(i)
    
    def create_mission(self, data:bytes, info:dict={}, extension:Optional[str]=None, buff:int=4096) -> str:
        """Create a send mission.
        
        Split large data into chunks and add to the send queue, each chunk will be sent separately.
        
        Args:
            data: Byte data to send
            info: Metadata related to the data
            extension: Optional extension identifier, defaults to a random secure code
            buff: Size of each data chunk, default is 4096 bytes
            
        Returns:
            str: The mission's extension identifier
        """
        with self.send_lock:  # 添加锁保护
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
        """Main function of the send thread.
        
        Continuously monitors the task queue and sends data, handling task headers and task data.
        """
        try:
            while True:
                # 接收线程错误时，停止发送线程
                if self.recv_exception:
                    self.recv_exception = False
                    self._send_error_handler('with_exception')
                    break
                
                with self.send_lock:  # 添加锁保护
                    send_pool_copy = list(self.send_pool.items())
                
                for extension, queue in send_pool_copy:
                    # 发送任务头
                    while not self.mission_head.empty():
                        mission = self.mission_head.get()
                        self._send(json.dumps(mission), {
                            'type': 'mission'
                        })
                        self.mission_head.task_done()
                    
                    with self.send_lock:  # 添加锁保护
                        info = self.misson_info[extension]
                    
                    # 发送任务数据
                    if queue.empty():
                        with self.send_lock:  # 添加锁保护
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
        """Main function of the receive thread.
        
        Continuously receives data, handles task headers and task data, assembles complete messages.
        """
        try:
            while True:
                lso, info = self._recv()
                if info['type'] == 'mission':
                    # 接收任务头
                    data = lso.json
                    with self.recv_lock:  # 添加锁保护
                        self.temp_pool[data['extension']] = {
                            'length': data['length'],
                            'recv': 0,
                            'data': bytearray(),
                        }
                        self.recv_info[data['extension']] = data['info']
                    continue
                
                # 接收任务数据
                with self.recv_lock:  # 添加锁保护
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
        """Handle errors during sending.
        
        Args:
            message: Error message type
            exception: Optional exception object
        """
        if message == 'error':
            logger.error(f'Pipe error: {exception}')
        if message == 'close':
            logger.info('Pipe closed.')
        if message == 'with_exception':
            logger.warning('Pipe closed with recv exception.')
        if self.final_error_handler:
            try:
                logger.info('Final error handler is running.')
                self.final_error_handler()
            except Exception as e:
                logger.error(f'Final error handler occurred error: {e}')

    def _recv_error_handler(self, message:str, exception:Exception=None):
        """Handle errors during receiving.
        
        Args:
            message: Error message type
            exception: Optional exception object
        """
        if message == 'error':
            logger.error(f'Pipe error: {exception}')
        if message == 'close':
            logger.info('Pipe closed.')
    
    def send(self, data:bytes, info:dict={}):
        """Send data and related information.
        
        Simplified version of create_mission, for quick data sending.
        
        Args:
            data: Byte data to send
            info: Metadata related to the data
        """
        self.create_mission(data, info)
    
    def recv(self) -> tuple[bytes, dict]:
        """Receive data and related information.
        
        Get a complete data packet from the receive pool.
        
        Returns:
            tuple: (data bytes, info dictionary)
        """
        with self.recv_lock:  # 添加锁保护
            if not self.recv_pool: 
                return None, None  # 修改返回值，防止解包错误
            extension, data = self.recv_pool.popitem()
            info = self.recv_info.pop(extension)
            info.update({
                'extension': extension
            })
            return data, info
    
    @property
    def is_data(self) -> bool:
        """Check if there is data available to receive.
        
        Returns:
            bool: True if there is data, False otherwise
        """
        with self.recv_lock:  # 添加锁保护
            return bool(self.recv_pool)
    
    def start(self):
        """Start the pipe's send and receive threads."""
        self.recv_thread.start()
        self.send_thread.start()
