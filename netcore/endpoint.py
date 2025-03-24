from .lso   import *
from typing import Any, Dict, Callable, List
from .event import EventEmitter
from .scheduler import Scheduler
from .cache import Cache
import json
import threading
import time
import logging
import functools

# 配置日志记录器
logger = logging.getLogger("netcore")

# 全局请求对象，用于在处理请求时访问
class Request:
    def __init__(self, meta: bytes = None):
        self.meta = meta if isinstance(meta, bytes) else bytes(meta)
        self.json = None
        self.string = None
        try:
            self.json = json.loads(self.meta)
        except:
            self.json = {}
        try:
            self.string = self.meta.decode('utf-8')
        except:
            self.string = ''

# 全局请求对象实例
request = Request(b'')

class Response:
    def __init__(self, route: str, data: Any) -> None:
        """创建响应对象
        
        Args:
            route: 响应的路由
            data: 响应的数据
        """
        self.route = route
        self.data = data
    
    def to_bytes(self) -> bytes:
        """将响应数据转换为字节"""
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
    def __init__(self, pipe: Pipe):
        """创建端点
        
        Args:
            pipe: 用于通信的管道
        """
        self.pipe = pipe
        self.routes: Dict[str, Callable] = {}
        self.running = False
        self.handler_thread = None
        self.default_handler = None  # 默认消息处理器
        self.response_handlers: Dict[str, Callable] = {}  # 响应处理器
        
        # 新增功能
        self.middlewares: List[Callable] = []  # 中间件列表
        self.error_handler = None  # 错误处理器
        self.before_request_funcs: List[Callable] = []  # 请求前钩子
        self.after_request_funcs: List[Callable] = []  # 请求后钩子
        
        self.event = EventEmitter()  # 事件系统
        self.scheduler = Scheduler()  # 定时任务系统
        self.cache = Cache()  # 缓存系统
    
    def request(self, route: str):
        """路由装饰器，用于注册处理不同路由的函数
        
        Args:
            route: 请求的路由名称
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper():
                try:
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
        """注册默认消息处理器，用于处理没有指定路由的消息
        
        Args:
            func: 处理函数
        """
        self.default_handler = func
        return func
    
    def middleware(self, func):
        """中间件装饰器
        
        Args:
            func: 中间件函数，接收handler作为参数，返回新的handler
        """
        self.middlewares.append(func)
        logger.debug(f"端点添加中间件 '{func.__name__}'")
        return func
    
    def error_handle(self, func):
        """错误处理装饰器
        
        Args:
            func: 错误处理函数，接收异常作为参数
        """
        self.error_handler = func
        logger.debug(f"端点设置错误处理器 '{func.__name__}'")
        return func
    
    def before_request(self, func):
        """请求前钩子装饰器
        
        Args:
            func: 在请求处理前执行的函数
        """
        self.before_request_funcs.append(func)
        logger.debug(f"端点添加请求前钩子 '{func.__name__}'")
        return func
    
    def after_request(self, func):
        """请求后钩子装饰器
        
        Args:
            func: 在请求处理后执行的函数，接收响应对象作为参数
        """
        self.after_request_funcs.append(func)
        logger.debug(f"端点添加请求后钩子 '{func.__name__}'")
        return func
    
    def _handle_requests(self):
        """处理接收到的请求"""
        global request
        
        while self.running:
            if not self.pipe.is_data:
                time.sleep(0.1)
                continue
                
            data, info = self.pipe.recv()
            if not data or not info:
                continue
            
            # 更新全局请求对象的属性，而不是创建新对象
            request.meta = data
            try:
                request.json = json.loads(data)
            except:
                request.json = {}
            try:
                request.string = data.decode('utf-8')
            except:
                request.string = ''
            
            # 处理消息ID的响应
            message_id = info.get('message_id')
            if message_id and message_id in self.response_handlers:
                try:
                    self.response_handlers[message_id](data, info)
                    del self.response_handlers[message_id]  # 处理完成后移除handler
                    continue
                except Exception as e:
                    logger.error(f"处理响应 ID '{message_id}' 时出错: {e}")
                    continue
            
            route = info.get('route', '')
            # 有路由的情况，调用对应的处理函数
            if route and route in self.routes:
                try:
                    result = self.routes[route]()
                    if isinstance(result, Response):
                        # 发送响应
                        self.pipe.send(result.to_bytes(), {
                            'route': result.route,
                            'is_response': True,
                            'message_id': info.get('message_id')  # 返回相同的消息ID
                        })
                except Exception as e:
                    if self.error_handler:
                        try:
                            result = self.error_handler(e)
                            if isinstance(result, Response):
                                self.pipe.send(result.to_bytes(), {
                                    'route': result.route,
                                    'is_response': True,
                                    'message_id': info.get('message_id')
                                })
                        except Exception as e2:
                            logger.error(f"错误处理器处理异常时出错: {e2}")
                    else:
                        logger.error(f"处理路由 '{route}' 时出错: {e}")
            # 没有路由或路由未注册，使用默认处理器
            elif self.default_handler:
                try:
                    self.default_handler(data, info)
                except Exception as e:
                    if self.error_handler:
                        try:
                            self.error_handler(e)
                        except Exception as e2:
                            logger.error(f"错误处理器处理异常时出错: {e2}")
                    else:
                        logger.error(f"默认处理器处理消息时出错: {e}")
            
            # 触发请求事件
            self.event.emit('request', data, info)
            
            # 处理响应后触发响应事件
            if isinstance(result, Response):
                self.event.emit('response', result)
    
    def send(self, route: str, data: Any, callback: Callable = None) -> str:
        """发送请求到对端
        
        Args:
            route: 请求的路由
            data: 请求的数据
            callback: 响应回调函数，接收 (data, info) 两个参数。如果存在，本次响应会覆盖设置的回调函数
            
        Returns:
            str: 消息ID
        """
        # 使用 Utils.safe_code 生成唯一的消息ID
        message_id = Utils.safe_code(8)
        
        # 如果有回调，注册到响应处理器
        if callback:
            self.response_handlers[message_id] = callback
        
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
        
        return message_id
    
    def send_response(self, data: Any, info: dict) -> None:
        """发送响应到对端
        
        Args:
            data: 响应数据
            info: 原始请求的信息
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
        """启动端点"""
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
        """停止端点"""
        self.running = False
        self.scheduler.stop()  # 停止调度器
        if self.handler_thread:
            self.handler_thread.join(timeout=1.0)
        # 触发停止事件
        self.event.emit('stop')
    
    def register_blueprint(self, blueprint):
        """注册蓝图到端点
        
        Args:
            blueprint: 要注册的蓝图实例
        """
        for route, handler in blueprint.routes.items():
            if route == f"{blueprint.prefix}/__default__":
                # 特殊处理默认路由
                if not self.default_handler:
                    self.default_handler = handler
                continue
            self.routes[route] = handler
        logger.info(f"端点注册蓝图 '{blueprint.name}'，共 {len(blueprint.routes)} 个路由")
        return self  # 返回self以支持链式调用
        
        