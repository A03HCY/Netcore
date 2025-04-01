from .lso       import *
from typing     import Any, Dict, Callable, List, Union
from .event     import EventEmitter
from .scheduler import Scheduler
from .cache     import Cache
from .error     import *

import json
import threading
import logging
import functools
import queue
from concurrent.futures import ThreadPoolExecutor

# 配置日志记录器
logger = logging.getLogger("netcore")

# 线程本地存储
_thread_local = threading.local()

# 请求类
class Request:
    """Request object class for accessing request information.
    
    Encapsulates the request data and provides convenient access to
    different formats of the request data. Supports JSON and string parsing,
    header information, and pipe source tracking for MultiPipe environments.
    
    Attributes:
        meta (bytes): Raw binary data of the request
        route (str): The request route or path
        message_id (str): Unique identifier for the request/response
        is_response (bool): Whether this request is a response to another request
        is_cancel (bool): Whether this request is a cancellation notification
        json (dict): Request data parsed as JSON (empty dict if invalid)
        string (str): Request data decoded as UTF-8 string (empty string if invalid)
    """
    
    def __init__(self, meta: bytes = None, info: dict = None):
        """Initialize a Request object.
        
        Args:
            meta: Raw binary data of the request
            info: Dictionary with request metadata/headers
        """
        info = info or {}
        self.meta = meta if isinstance(meta, bytes) else bytes(meta or b'')
        self.json = None
        self.string = None
        self.route = info.get('route', '')
        self.message_id = info.get('message_id', '')
        self._pipe_safe_code = info.get('pipe_safe_code', None)
        self.is_response = info.get('is_response', False)
        self.is_cancel = info.get('is_cancel', False)
        self._headers = {k: v for k, v in info.items() 
                        if k not in ['route', 'message_id', 'pipe_safe_code', 
                                    'is_response', 'is_cancel']}
        self._parse()
    
    def _parse(self):
        """Parse the raw data into different formats."""
        # 解析JSON
        try:
            self.json = json.loads(self.meta)
        except (json.JSONDecodeError, TypeError, ValueError):
            self.json = {}
            
        # 解析字符串
        try:
            self.string = self.meta.decode('utf-8')
        except (UnicodeDecodeError, AttributeError):
            self.string = ''
    
    @property
    def pipe_safe_code(self):
        """Get the pipe safe code that identifies the source pipe in MultiPipe setup.
        
        Returns:
            str: The pipe safe code or None if not available
        """
        return self._pipe_safe_code
    
    @property
    def headers(self):
        """Get all request headers/metadata.
        
        Returns:
            dict: All headers not handled as special attributes
        """
        return self._headers
    
    def get_header(self, key, default=None):
        """Get a specific header value.
        
        Args:
            key: Header key to retrieve
            default: Default value if key doesn't exist
            
        Returns:
            Value of the header or default if not found
        """
        return self._headers.get(key, default)
    
    def get_json(self, key=None, default=None):
        """Get JSON data or a specific field from JSON data.
        
        Args:
            key: Specific JSON key to retrieve (optional)
            default: Default value if key doesn't exist
            
        Returns:
            The entire JSON dict if key is None, or the value for the specific key
        """
        if key is None:
            return self.json
        return self.json.get(key, default) if isinstance(self.json, dict) else default
    
    def __str__(self):
        """String representation of the request.
        
        Returns:
            str: A summary of the request including route and message ID
        """
        type_str = "Response" if self.is_response else "Request"
        status = " (Cancelled)" if self.is_cancel else ""
        return f"{type_str}{status}: route='{self.route}', message_id='{self.message_id}'"
    
    def __repr__(self):
        """Developer representation of the request.
        
        Returns:
            str: A detailed representation of the request for debugging
        """
        return (f"Request(route='{self.route}', message_id='{self.message_id}', "
                f"is_response={self.is_response}, is_cancel={self.is_cancel}, "
                f"pipe_safe_code={self._pipe_safe_code!r}, "
                f"meta_length={len(self.meta)})")
    
    def size(self):
        """Get the size of the request data.
        
        Returns:
            int: Size of the request data in bytes
        """
        return len(self.meta)
    
    def is_json(self):
        """Check if the request contains valid JSON data.
        
        Returns:
            bool: True if the request contains valid JSON, False otherwise
        """
        return bool(self.json)
    
    def is_empty(self):
        """Check if the request is empty.
        
        Returns:
            bool: True if the request contains no data, False otherwise
        """
        return len(self.meta) == 0

# 请求代理类 - 类似Flask的实现
class RequestProxy:
    """Request proxy object, automatically retrieves the current request from thread-local storage.
    
    Similar to Flask's implementation, allows accessing the current request
    from anywhere in the code, while maintaining thread safety.
    """
    
    def __getattr__(self, name) -> Request:
        if not hasattr(_thread_local, 'request'):
            _thread_local.request = Request(b'')
        return getattr(_thread_local.request, name)
    
    def __setattr__(self, name, value):
        if not hasattr(_thread_local, 'request'):
            _thread_local.request = Request(b'')
        setattr(_thread_local.request, name, value)

# 设置当前线程的请求对象
def set_request(req):
    """Set the request object for the current thread.
    
    Args:
        req: The Request object to set as the current thread's request
    """
    _thread_local.request = req

# 全局请求对象 - 现在是一个代理
request: Request = RequestProxy()

class Response:
    """Response object for returning data to the client.
    
    Encapsulates the response data and provides methods to convert
    the response to the appropriate format.
    """
    
    def __init__(self, route: str, data: Any) -> None:
        """Create a response object.
        
        Args:
            route: The response route
            data: The response data
        """
        self.route = route
        self.data = data
    
    def to_bytes(self) -> bytes:
        """Convert response data to bytes format.
        
        Returns:
            bytes: The response data in bytes format
        """
        if isinstance(self.data, dict):
            return json.dumps(self.data).encode('utf-8')
        elif isinstance(self.data, str):
            return self.data.encode('utf-8')
        elif isinstance(self.data, bytes):
            return self.data
        elif isinstance(self.data, bytearray):
            return self.data
        else:
            return str(self.data).encode('utf-8')


class MultiPipe:
    """MultiPipe class for managing multiple communication pipes.
    
    Allows an endpoint to communicate through multiple pipes simultaneously,
    providing pipe pooling and management capabilities.
    """
    def __init__(self):
        self.pipe_pool: Dict[str, Pipe] = {}
        self.pipe_info: Dict[str, dict] = {}
        self.pipe_lock = threading.RLock()
        self.info_lock = threading.RLock()
            
        self.final_error_handler: Callable = None
        self.cancel_handler: Callable[[str], None] = self._cancel_handler
        self.mission_complete_handler: Callable[[str], None] = self._mission_complete_handler
        
        # 添加接收队列，用于存储来自所有管道的数据
        self.recv_queue = queue.Queue()
        self.recv_threads = {}
        self.running = False
        self._recv_exception = None
    
    def __call__(self, safe_code: str) -> Pipe:
        return self.get_pipe(safe_code)[0]

    def add_pipe(self, pipe: Pipe, safe_code: str = None):
        """添加一个管道到管道池
        
        Args:
            pipe: 要添加的管道对象
            safe_code: 可选的安全码，如果不提供则自动生成
        
        Returns:
            str: 管道的安全码
        """
        if safe_code is None:
            safe_code = Utils.safe_code(6)
        
        with self.pipe_lock:
            self.pipe_pool[safe_code] = pipe
        with self.info_lock:
            self.pipe_info[safe_code] = {
                'running': False,
                'safe_code': safe_code
            }
        
        # 设置管道的处理器
        pipe.final_error_handler = self.final_error_handler
        pipe.cancel_handler = self.cancel_handler
        pipe.mission_complete_handler = self.mission_complete_handler
        
        return safe_code
    
    def get_pipe(self, safe_code: str) -> Tuple[Pipe, dict]:
        """获取指定安全码的管道和信息
        
        Args:
            safe_code: 管道的安全码
            
        Returns:
            Tuple[Pipe, dict]: 管道对象和管道信息
        """
        with self.info_lock:
            info = self.pipe_info.get(safe_code, None)
        with self.pipe_lock:
            return self.pipe_pool.get(safe_code, None), info
            
    def remove_pipe(self, safe_code: str) -> bool:
        """移除指定安全码的管道
        
        Args:
            safe_code: 管道的安全码
            
        Returns:
            bool: 是否成功移除
        """
        with self.pipe_lock:
            if safe_code in self.pipe_pool:
                pipe = self.pipe_pool.pop(safe_code)
                # 停止管道
                if pipe:
                    try:
                        pipe.stop()
                    except:
                        pass
        
        with self.info_lock:
            if safe_code in self.pipe_info:
                del self.pipe_info[safe_code]
                return True
        
        # 停止接收线程
        if safe_code in self.recv_threads:
            self.recv_threads.pop(safe_code)
        
        return False
    
    def clear(self):
        """清空所有管道"""
        # 停止所有管道
        with self.pipe_lock:
            for pipe in self.pipe_pool.values():
                try:
                    pipe.stop()
                except:
                    pass
            self.pipe_pool.clear()
        
        with self.info_lock:
            self.pipe_info.clear()
        
        # 清空接收线程
        self.recv_threads.clear()
    
    def start(self):
        """启动所有管道"""
        self.running = True
        
        with self.pipe_lock:
            with self.info_lock:
                for safe_code, pipe in self.pipe_pool.items():
                    pipe.final_error_handler = self.final_error_handler
                    pipe.cancel_handler = self.cancel_handler
                    pipe.mission_complete_handler = self.mission_complete_handler
                    
                    # 启动管道
                    pipe.start()
                    self.pipe_info[safe_code]['running'] = True
                    
                    # 为每个管道创建接收线程
                    self._start_recv_thread(safe_code, pipe)
    
    def stop(self):
        """停止所有管道"""
        self.running = False
        
        # 停止所有管道
        with self.pipe_lock:
            for pipe in self.pipe_pool.values():
                try:
                    pipe.stop()
                except:
                    pass
                
        # 等待所有接收线程结束
        for thread in self.recv_threads.values():
            if thread and thread.is_alive():
                thread.join(timeout=1.0)
    
    def _start_recv_thread(self, safe_code, pipe):
        """为指定管道启动接收线程
        
        Args:
            safe_code: 管道的安全码
            pipe: 管道对象
        """
        thread = threading.Thread(
            target=self._pipe_recv_thread,
            args=(safe_code, pipe),
            daemon=True
        )
        thread.start()
        self.recv_threads[safe_code] = thread
    
    def _pipe_recv_thread(self, safe_code, pipe):
        """管道接收线程函数
        
        从指定管道接收数据并放入接收队列
        
        Args:
            safe_code: 管道的安全码
            pipe: 管道对象
        """
        try:
            while self.running:
                if not pipe.is_data:
                    if pipe.recv_exception:
                        logger.error(f"Pipe {safe_code} receive exception: {pipe.recv_exception}")
                        self._recv_exception = pipe.recv_exception
                        continue
                    continue
                
                data, info = pipe.recv()
                if not data or not info:
                    continue
                
                # 将管道安全码添加到info中
                info['pipe_safe_code'] = safe_code
                
                # 放入接收队列
                self.recv_queue.put((data, info))
        except Exception as e:
            logger.error(f"Pipe {safe_code} thread error: {e}")
            self._recv_exception = e
    
    def _mission_complete_handler(self, extension: str) -> None:
        """任务完成处理器
        
        Args:
            extension: 任务标识符
        """
        pass

    def _cancel_handler(self, extension: str) -> None:
        """任务取消处理器
        
        Args:
            extension: 任务标识符
        """
        pass
    
    def recv(self):
        """从接收队列中获取数据
        
        Returns:
            Tuple[bytes, dict]: 接收到的数据和信息
        """
        try:
            return self.recv_queue.get(block=False)
        except queue.Empty:
            return None, None
    
    def send(self, data, info, safe_code=None):
        """发送数据到指定管道
        
        Args:
            data: 要发送的数据
            info: 关联的信息
            safe_code: 指定的管道安全码，如果不提供则使用第一个可用管道
            
        Returns:
            str: 任务标识符
        """
        if safe_code is not None:
            with self.pipe_lock:
                pipe = self.pipe_pool.get(safe_code)
                if pipe:
                    return pipe.send(data, info)
                else:
                    logger.error(f"Pipe with safe_code {safe_code} not found")
                    return None
        else:
            # 使用第一个可用管道
            with self.pipe_lock:
                if not self.pipe_pool:
                    logger.error("No pipes available")
                    return None
                
                # 获取第一个管道
                first_safe_code = next(iter(self.pipe_pool))
                pipe = self.pipe_pool[first_safe_code]
                return pipe.send(data, info)
    
    def cancel_mission(self, extension, safe_code=None):
        """取消指定任务
        
        Args:
            extension: 任务标识符
            safe_code: 指定的管道安全码，如果不提供则在所有管道中搜索
            
        Returns:
            bool: 是否成功取消
        """
        if safe_code is not None:
            with self.pipe_lock:
                pipe = self.pipe_pool.get(safe_code)
                if pipe:
                    return pipe.cancel_mission(extension)
                else:
                    logger.error(f"Pipe with safe_code {safe_code} not found")
                    return False
        else:
            # 在所有管道中搜索并取消
            with self.pipe_lock:
                for pipe in self.pipe_pool.values():
                    if pipe.cancel_mission(extension):
                        return True
                return False
    
    @property
    def is_data(self):
        """检查是否有数据可用
        
        Returns:
            bool: 是否有数据可用
        """
        return not self.recv_queue.empty()
    
    @property
    def recv_exception(self):
        """获取接收异常
        
        Returns:
            Exception: 接收过程中的异常
        """
        return self._recv_exception


class Endpoint:
    """Endpoint class for handling network communication.
    
    Manages routes, middleware, hooks, and communicates through the provided pipe.
    Supports multithreaded request handling for increased performance.
    """
    
    def __init__(self, pipe: Pipe|MultiPipe, max_workers: int = 1):
        """Create an endpoint.
        
        Args:
            pipe: Communication pipe or MultiPipe instance
            max_workers: Number of worker threads, defaults to 1
        """
        self.pipe = pipe
        self.pipe.final_error_handler = self.stop
        self.pipe.cancel_handler = self._cancel_handler
        self.routes: Dict[str, Callable] = {}
        self.running = False
        self.handler_thread = None
        self.default_handler = None  # 默认消息处理器
        self.response_handlers: Dict[str, Callable] = {}  # 响应处理器
        
        self.blocking_recv: Dict[str, Request] = {}  # 阻塞收消息

        self.middlewares: List[Callable] = []  # 中间件列表
        self.error_handler = None  # 错误处理器
        self.before_request_funcs: List[Callable] = []  # 请求前钩子
        self.after_request_funcs: List[Callable] = []  # 请求后钩子
        
        self.event = EventEmitter()  # 事件系统
        self.scheduler = Scheduler()  # 定时任务系统
        self.cache = Cache()  # 缓存系统
        
        # 多线程支持
        self.max_workers = max_workers
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.request_queue = queue.Queue()
        self.lock = threading.RLock()  # 可重入锁
        
        # 添加extension到message_id的映射，用于处理任务取消
        self.extension_to_message = {}
        
        # 添加message_id到pipe_safe_code的映射，用于支持MultiPipe
        self.message_to_pipe = {}
        
        # 是否使用MultiPipe
        self.is_multi_pipe = isinstance(pipe, MultiPipe)
    
    def request(self, route: str):
        """Route decorator for registering functions to handle different routes.
        
        Args:
            route: The route path to handle
            
        Returns:
            A decorator function
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper():
                try:
                    # 请求对象已经通过线程本地存储设置好了
                    # 不需要显式获取
                    
                    # 执行请求前钩子
                    for before_func in self.before_request_funcs:
                        before_result = before_func()
                        if before_result is not None:
                            return before_result
                    
                    print(self.middlewares)
                    # 执行中间件链
                    handler = func
                    for middleware in self.middlewares:
                        print('Middleware:', middleware)
                        handler = middleware(handler)
                    
                    # 执行实际处理函数
                    result = handler()

                    # 执行请求后钩子
                    for after_func in self.after_request_funcs:
                        after_result = after_func(result)
                        if after_result is not None:
                            result = after_result
                    return result
                except Exception as e:
                    # 执行错误处理
                    if self.error_handler:
                        return self.error_handler(e)
                    raise EndpointMiddlewareError('Endpoint middleware error', e)
            
            self.routes[route] = wrapper
            return func
        return decorator
    
    def default(self, func):
        """Register a default message handler for messages without a specific route.
        
        Args:
            func: The handler function
            
        Returns:
            The original function for chaining
        """
        self.default_handler = func
        return func
    
    def middleware(self, func):
        """Middleware decorator.
        
        Args:
            func: Middleware function that takes a handler and returns a new handler
            
        Returns:
            The original function for chaining
        """
        self.middlewares.append(func)
        logger.debug(f"Endpoint added middleware '{func.__name__}'")
        return func
    
    def error_handle(self, func):
        """Error handler decorator.
        
        Args:
            func: Error handling function that takes an exception as parameter
            
        Returns:
            The original function for chaining
        """
        self.error_handler = func
        logger.debug(f"Endpoint set error handler '{func.__name__}'")
        return func
    
    def before_request(self, func):
        """Before request hook decorator.
        
        Args:
            func: Function to execute before request processing
            
        Returns:
            The original function for chaining
        """
        self.before_request_funcs.append(func)
        logger.debug(f"Endpoint added before request hook '{func.__name__}'")
        return func
    
    def after_request(self, func):
        """After request hook decorator.
        
        Args:
            func: Function to execute after request processing, receives response as parameter
            
        Returns:
            The original function for chaining
        """
        self.after_request_funcs.append(func)
        logger.debug(f"Endpoint added after request hook '{func.__name__}'")
        return func
    
    def _handle_requests(self):
        """Handle incoming requests by distributing them to worker threads."""
        global request
        
        worker_threads = []
        # 启动工作线程
        for _ in range(self.max_workers):
            thread = threading.Thread(target=self._worker_thread)
            thread.daemon = True
            thread.start()
            worker_threads.append(thread)
            
        while self.running:
            if not self.pipe.is_data:
                if self.pipe.recv_exception:
                    logger.error(f"Pipe receive exception: {self.pipe.recv_exception}")
                    logger.info("Endpoint stopped")
                    self.event.emit('recv_exception')
                    self.stop()
                continue
                
            data, info = self.pipe.recv()
            if not data or not info:
                break
            
            # 将请求放入队列，由工作线程处理
            self.request_queue.put((data, info))
        
        # 等待所有工作线程结束
        for _ in range(self.max_workers):
            self.request_queue.put(None)  # 发送结束信号
        for thread in worker_threads:
            thread.join()
    
    def _worker_thread(self):
        """Worker thread function that processes requests from the queue."""
        while self.running:
            task = self.request_queue.get()
            if task is None:  # 结束信号
                self.request_queue.task_done()
                break
                
            data, info = task
            
            # 创建线程本地的请求对象
            thread_request = Request(data, info)
            set_request(thread_request)  # 设置线程本地请求对象
            
            # 处理消息ID的响应
            message_id = thread_request.message_id
            with self.lock:
                if message_id and message_id in self.response_handlers:
                    try:
                        self.response_handlers[message_id](thread_request)
                        del self.response_handlers[message_id]  # 处理完成后移除handler
                        
                        # 如果存在，清理message_id到pipe的映射
                        if message_id in self.message_to_pipe:
                            del self.message_to_pipe[message_id]
                            
                        self.request_queue.task_done()
                        continue
                    except Exception as e:
                        logger.error(f"Error processing response ID '{message_id}': {e}")
                        # 清理映射
                        if message_id in self.message_to_pipe:
                            del self.message_to_pipe[message_id]
                        self.request_queue.task_done()
                        continue
            
            route = thread_request.route
            result = None
            
            # 有路由的情况，调用对应的处理函数
            if route and route in self.routes:
                try:
                    # 不再需要替换全局请求对象，直接使用线程本地存储
                    result = self.routes[route]()
                    
                    if isinstance(result, Response):
                        # 发送响应，如果有pipe_safe_code，使用指定的pipe
                        self._send_response_with_pipe(result, thread_request)
                except Exception as e:
                    if self.error_handler:
                        try:
                            result = self.error_handler(e)
                            if isinstance(result, Response):
                                self._send_response_with_pipe(result, thread_request)
                        except Exception as e2:
                            logger.error(f"Error handler encountered an error: {e2}")
                    else:
                        logger.error(f"Error processing route '{route}': {e}")
            # 没有路由或路由未注册，使用默认处理器
            elif self.default_handler:
                try:
                    # 不再需要替换全局请求对象
                    self.default_handler()
                except Exception as e:
                    if self.error_handler:
                        try:
                            self.error_handler(e)
                        except Exception as e2:
                            logger.error(f"Error processing route '{route}': {e}")
                    else:
                        logger.error(f"Default handler encountered an error processing message: {e}")
            
            # 触发请求事件
            self.event.emit('request', thread_request)
            
            # 处理响应后触发响应事件
            if isinstance(result, Response):
                self.event.emit('response', result)
                
            self.request_queue.task_done()
    
    def _send_response_with_pipe(self, response, request):
        """使用指定管道发送响应
        
        Args:
            response: 响应对象
            request: 请求对象
            pipe_safe_code: 管道安全码
        """
        # 准备响应数据
        data_bytes = response.to_bytes()
        info = {
            'route': response.route,
            'is_response': True,
            'message_id': request.message_id
        }
        
        # 如果是MultiPipe且有pipe_safe_code，使用指定的pipe
        if self.is_multi_pipe and request.pipe_safe_code:
            self.pipe.send(data_bytes, info, request.pipe_safe_code)
        else:
            self.pipe.send(data_bytes, info)

    def _blocking_recv_save_data(self, request:Request):
        """Save received data for blocking receive operations."""
        self.blocking_recv[request.message_id] = request
    
    def _blocking_recv(self, message_id:str):
        """Wait for and retrieve response data for blocking receive operations."""
        # 等待响应数据到达或被取消
        while True:
            with self.lock:
                if message_id in self.blocking_recv:
                    request = self.blocking_recv.pop(message_id)
                    # 检查是否是取消消息
                    if request.is_cancel == True:
                        # 返回取消响应
                        logger.info(f"Blocking receive for {message_id} was cancelled")
                    return request
    
    def _mission_complete_handler(self, extension: str) -> None:
        """Handle mission completion.
        
        Args:
            extension: The extension identifier of the task that has completed
        """
        with self.lock:
            if extension in self.blocking_recv:
                self.blocking_recv.pop(extension)
    
    def _cancel_handler(self, extension: str) -> None:
        """Handle mission cancellation.
        
        When a mission is cancelled by the remote endpoint, this handler will notify
        any waiting blocking receives with a cancellation response.
        
        Args:
            extension: The extension identifier of the transmission task to cancel
        """
        with self.lock:
            # 查找对应的message_id
            if extension not in self.extension_to_message:
                logger.debug(f"Received cancellation for unknown extension: {extension}")
                return
            
            message_id = self.extension_to_message.pop(extension)
            
            cancel_request = Request(
                json.dumps({
                    "status": "cancelled",
                    "message": "Mission was cancelled by the remote endpoint"
                }).encode('utf-8'),
                {"is_response": True, "message_id": message_id, "is_cancel": True}
            )
            
            # 如果有阻塞接收在等待这个消息，发送取消通知
            if message_id in self.response_handlers:
                # 调用原本的响应处理器
                try:
                    self.response_handlers[message_id](cancel_request)
                    del self.response_handlers[message_id]
                    logger.info(f"Notified waiting handler for message {message_id} about cancellation")
                except Exception as e:
                    logger.error(f"Error notifying response handler about cancellation: {e}")

    def send(self, route: str, data: Any, callback: Callable = None, blocking_recv:bool=False, pipe_safe_code:str=None) -> Union[str, Request, Dict[str, str]]:
        """Send a request to the remote endpoint.
        
        Args:
            route: The route to send the request to
            data: The request data
            callback: Optional response callback function that takes (data, info) parameters
            blocking_recv: If True, wait for and return the response
            pipe_safe_code: Optional pipe safe code for MultiPipe
            
        Returns:
            str: Message ID if not blocking
            Request: Response request object if blocking
            Dict[str, str]: Dictionary containing both message_id and mission_extension if the data is large
        """
        # 使用 Utils.safe_code 生成唯一的消息ID
        message_id = Utils.safe_code(8)
        
        # 如果有回调，注册到响应处理器
        with self.lock:
            if callback and blocking_recv == False:
                self.response_handlers[message_id] = callback
            if blocking_recv == True:
                self.response_handlers[message_id] = self._blocking_recv_save_data
            
            # 保存message_id到pipe_safe_code的映射（如果使用MultiPipe）
            if self.is_multi_pipe and pipe_safe_code:
                self.message_to_pipe[message_id] = pipe_safe_code
        
        # 发送数据
        if isinstance(data, dict):
            data_bytes = json.dumps(data).encode('utf-8')
        elif isinstance(data, str):
            data_bytes = data.encode('utf-8')
        elif isinstance(data, bytes):
            data_bytes = data
        else:
            data_bytes = json.dumps({"data": str(data)}).encode('utf-8')
            
        # 获取发送任务的extension标识符
        if self.is_multi_pipe and pipe_safe_code:
            mission_extension = self.pipe.send(data_bytes, {
                'route': route,
                'message_id': message_id
            }, pipe_safe_code)
        else:
            mission_extension = self.pipe.send(data_bytes, {
                'route': route,
                'message_id': message_id
            })

        # 如果返回的extension与message_id不同，说明是大数据任务
        # 存储它们之间的映射关系
        if mission_extension != message_id:
            with self.lock:
                self.extension_to_message[mission_extension] = message_id
        
        if blocking_recv:
            return self._blocking_recv(message_id)
        
        # 如果mission_extension不是message_id，说明是大数据任务
        # 返回包含message_id和mission_extension的字典，以便用户可以取消任务
        if mission_extension != message_id:
            return {
                'message_id': message_id,
                'mission_extension': mission_extension,
                'pipe_safe_code': pipe_safe_code if self.is_multi_pipe else None
            }
        
        return message_id
    
    def send_response(self, data: Any, info: dict) -> None:
        """Send a response back to the remote endpoint.
        
        Args:
            data: The response data
            info: The original request info
        """
        # 获取pipe_safe_code（如果使用MultiPipe）
        pipe_safe_code = info.get('pipe_safe_code', None)
        
        if isinstance(data, dict):
            data_bytes = json.dumps(data).encode('utf-8')
        elif isinstance(data, str):
            data_bytes = data.encode('utf-8')
        elif isinstance(data, bytes):
            data_bytes = data
        else:
            data_bytes = json.dumps({"data": str(data)}).encode('utf-8')
            
        # 如果是MultiPipe且有pipe_safe_code，使用指定的pipe
        if self.is_multi_pipe and pipe_safe_code:
            self.pipe.send(data_bytes, {
                'is_response': True,
                'message_id': info.get('message_id')
            }, pipe_safe_code)
        else:
            self.pipe.send(data_bytes, {
                'is_response': True,
                'message_id': info.get('message_id')
            })
    
    def start(self, block: bool = True):
        """Start the endpoint.
        
        Args:
            block: If True, block the current thread until the endpoint stops
        """
        self.pipe.start()
        self.running = True
        # 触发启动事件
        self.scheduler.start()
        # 触发启动事件
        self.event.emit('start')
        self.handler_thread = threading.Thread(target=self._handle_requests)
        self.handler_thread.daemon = True
        self.handler_thread.start()
        
        
        if block:
            self.handler_thread.join()
            
    def stop(self):
        """Stop the endpoint and release resources."""
        # 使用锁确保只执行一次
        with self.lock:
            if not self.running:  # 如果已经停止，直接返回
                return
            
            self.running = False
            self.scheduler.stop()  # 停止调度器
            
            # 添加检查，避免线程加入自己
            current_thread = threading.current_thread()
            if self.handler_thread and self.handler_thread != current_thread:
                self.handler_thread.join(timeout=1.0)
            
            # 触发停止事件
            self.event.emit('stop')
            
            logger.info("Endpoint stopped")
    
    def register_blueprint(self, blueprint):
        """Register a blueprint with this endpoint.
        
        Args:
            blueprint: The blueprint instance to register
            
        Returns:
            self: The endpoint instance for chaining
        """
        # 先注册蓝图的中间件和钩子
        for middleware in blueprint.middlewares:
            if middleware not in self.middlewares:
                self.middlewares.append(middleware)
                logger.debug(f"Blueprint '{blueprint.name}' added middleware '{middleware.__name__}'")

        for hook in blueprint.before_request_funcs:
            if hook not in self.before_request_funcs:
                self.before_request_funcs.append(hook)
                logger.debug(f"Blueprint '{blueprint.name}' added before request hook '{hook.__name__}'")
        
        for hook in blueprint.after_request_funcs:
            if hook not in self.after_request_funcs:
                self.after_request_funcs.append(hook)
                logger.debug(f"Blueprint '{blueprint.name}' added after request hook '{hook.__name__}'")
        
        # 如果蓝图有错误处理器且端点没有，也注册它
        if blueprint.error_handler and not self.error_handler:
            self.error_handler = blueprint.error_handler
            logger.debug(f"Blueprint '{blueprint.name}' set error handler '{blueprint.error_handler.__name__}'")
        
        # 注册路由处理函数
        for route, handler in blueprint.routes.items():
            if route == f"{blueprint.prefix}/__default__":
                # 特殊处理默认路由
                if not self.default_handler:
                    self.default_handler = handler
                continue
            
            # 为每个路由创建包装器，使用endpoint的机制来包装函数
            @functools.wraps(handler)
            def wrapper():
                try:
                    # 执行请求前钩子
                    for before_func in self.before_request_funcs:
                        before_result = before_func()
                        if before_result is not None:
                            return before_result
                    
                    # 执行中间件链
                    route_handler = handler
                    for middleware in self.middlewares:
                        route_handler = middleware(route_handler)
                    
                    # 执行实际处理函数
                    result = route_handler()
                    
                    # 执行请求后钩子
                    for after_func in self.after_request_funcs:
                        after_result = after_func(result)
                        if after_result is not None:
                            result = after_result
                    return result
                except Exception as e:
                    # 执行错误处理
                    if self.error_handler:
                        return self.error_handler(e)
                    raise EndpointMiddlewareError('Endpoint middleware error', e)
            
            self.routes[route] = wrapper
        
        logger.info(f"Endpoint registered blueprint '{blueprint.name}' with {len(blueprint.routes)} routes")
        return self  # 返回self以支持链式调用
        
    def cancel_mission(self, extension: str, pipe_safe_code: str = None) -> bool:
        """Cancel a specific transmission task.
        
        Removes the task from the send queue and sends a cancellation message to the remote endpoint.
        
        Args:
            extension: The extension identifier of the task to cancel
            pipe_safe_code: Optional pipe safe code for MultiPipe
            
        Returns:
            bool: True if the task was found and canceled, False otherwise
        """
        # 使用锁保护取消操作
        with self.lock:
            # 调用底层pipe的cancel_mission方法
            if self.is_multi_pipe and pipe_safe_code:
                result = self.pipe.cancel_mission(extension, pipe_safe_code)
            else:
                result = self.pipe.cancel_mission(extension)
            
            if result:
                # 如果取消成功，触发任务取消事件
                self.event.emit('mission_canceled', extension)
                logger.info(f"Endpoint canceled mission: {extension}")
            else:
                logger.warning(f"Endpoint failed to cancel mission: {extension}")
            
            return result
        