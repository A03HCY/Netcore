from typing import Callable, Union, Optional, Generator, Tuple
from struct import pack, unpack
from sys    import version_info as build_version
from os     import path, read as osread
from mmap   import mmap, ACCESS_WRITE


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
        return self._extension.decode(self.encoding)
    
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
    def extension(self) -> str:
        """
        获取当前扩展名。

        Returns:
            str: 扩展名的字符串。
        """
        return self._extension.decode(encoding=self.encoding)
    
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
            self._add_meta(head)  # 将头部数据添加到元数据中
        else:
            # 从流中接收头部信息
            extension_length = unpack('i', self.function_recv(function=function, length=4, handler=self._add_meta, buff=buff))[0]
            extension = self.function_recv(function=function, length=extension_length, handler=self._add_meta, buff=buff).decode(self.encoding)
            meta_length = unpack('i', self.function_recv(function=function, length=4, handler=self._add_meta, buff=buff))[0]
            
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
        