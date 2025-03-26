from .lso       import *
from typing     import Any, Dict, Callable, List
from .event     import EventEmitter
from .scheduler import Scheduler
from .cache     import Cache

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
    different formats of the request data.
    """
    
    def __init__(self, meta: bytes = None, info: dict = None):
        self.meta = meta if isinstance(meta, bytes) else bytes(meta)
        self.json = None
        self.string = None
        self.route = info.get('route', '')
        self.message_id = info.get('message_id', '')
        self.is_response = info.get('is_response', False)
        try:
            self.json = json.loads(self.meta)
        except:
            self.json = {}
        try:
            self.string = self.meta.decode('utf-8')
        except:
            self.string = ''

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

class Endpoint:
    """Endpoint class for handling network communication.
    
    Manages routes, middleware, hooks, and communicates through the provided pipe.
    Supports multithreaded request handling for increased performance.
    """
    
    def __init__(self, pipe: Pipe, max_workers: int = 1):
        """Create an endpoint.
        
        Args:
            pipe: Communication pipe
            max_workers: Number of worker threads, defaults to 1
        """
        self.pipe = pipe
        self.pipe.final_error_handler = self.stop
        self.routes: Dict[str, Callable] = {}
        self.running = False
        self.handler_thread = None
        self.default_handler = None  # 默认消息处理器
        self.response_handlers: Dict[str, Callable] = {}  # 响应处理器
        
        self.blocking_recv: Dict[str, Request] = {}  # 阻塞收消息

        # 新增功能
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
                    
                    # 执行中间件链
                    handler = func
                    for middleware in reversed(self.middlewares):
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
                    raise  # 如果没有错误处理器，重新抛出异常
            
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
                        self.request_queue.task_done()
                        continue
                    except Exception as e:
                        logger.error(f"Error processing response ID '{message_id}': {e}")
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
                        # 发送响应
                        self.pipe.send(result.to_bytes(), {
                            'route': result.route,
                            'is_response': True,
                            'message_id': thread_request.message_id  # 返回相同的消息ID
                        })
                except Exception as e:
                    if self.error_handler:
                        try:
                            result = self.error_handler(e)
                            if isinstance(result, Response):
                                self.pipe.send(result.to_bytes(), {
                                    'route': result.route,
                                    'is_response': True,
                                    'message_id': thread_request.message_id
                                })
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

    def _blocking_recv_save_data(self, request:Request):
        """Save received data for blocking receive operations."""
        self.blocking_recv[request.message_id] = request
    
    def _blocking_recv(self, message_id:str):
        """Wait for and retrieve response data for blocking receive operations."""
        while message_id not in self.blocking_recv.keys():
            pass
        return self.blocking_recv.pop(message_id)
    
    def send(self, route: str, data: Any, callback: Callable = None, blocking_recv:bool=False) -> str|Request:
        """Send a request to the remote endpoint.
        
        Args:
            route: The route to send the request to
            data: The request data
            callback: Optional response callback function that takes (data, info) parameters
            blocking_recv: If True, wait for and return the response
            
        Returns:
            str: Message ID if not blocking
            Request: Response request object if blocking
        """
        # 使用 Utils.safe_code 生成唯一的消息ID
        message_id = Utils.safe_code(8)
        
        # 如果有回调，注册到响应处理器
        with self.lock:
            if callback and blocking_recv == False:
                self.response_handlers[message_id] = callback
            if blocking_recv == True:
                self.response_handlers[message_id] = self._blocking_recv_save_data
        
        # 发送数据
        if isinstance(data, dict):
            data_bytes = json.dumps(data).encode('utf-8')
        elif isinstance(data, str):
            data_bytes = data.encode('utf-8')
        elif isinstance(data, bytes):
            data_bytes = data
        else:
            data_bytes = json.dumps({"data": str(data)}).encode('utf-8')
            
        self.pipe.send(data_bytes, {
            'route': route,
            'message_id': message_id
        })

        if blocking_recv:
            return self._blocking_recv(message_id)
        
        return message_id
    
    def send_response(self, data: Any, info: dict) -> None:
        """Send a response back to the remote endpoint.
        
        Args:
            data: The response data
            info: The original request info
        """
        if isinstance(data, dict):
            data_bytes = json.dumps(data).encode('utf-8')
        elif isinstance(data, str):
            data_bytes = data.encode('utf-8')
        elif isinstance(data, bytes):
            data_bytes = data
        else:
            data_bytes = json.dumps({"data": str(data)}).encode('utf-8')
            
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
        self.scheduler.start()  # 启动调度器
        self.handler_thread = threading.Thread(target=self._handle_requests)
        self.handler_thread.daemon = True
        self.handler_thread.start()
        
        # 触发启动事件
        self.event.emit('start')
        
        if block:
            self.handler_thread.join()
            
    def stop(self):
        """Stop the endpoint and release resources."""
        self.running = False
        self.scheduler.stop()  # 停止调度器
        
        # 添加检查，避免线程加入自己
        current_thread = threading.current_thread()
        if self.handler_thread and self.handler_thread != current_thread:
            self.handler_thread.join(timeout=1.0)
        
        # 触发停止事件
        self.event.emit('stop')
    
    def register_blueprint(self, blueprint):
        """Register a blueprint with this endpoint.
        
        Args:
            blueprint: The blueprint instance to register
            
        Returns:
            self: The endpoint instance for chaining
        """
        for route, handler in blueprint.routes.items():
            if route == f"{blueprint.prefix}/__default__":
                # 特殊处理默认路由
                if not self.default_handler:
                    self.default_handler = handler
                continue
            self.routes[route] = handler
        logger.info(f"Endpoint registered blueprint '{blueprint.name}' with {len(blueprint.routes)} routes")
        return self  # 返回self以支持链式调用
        
        