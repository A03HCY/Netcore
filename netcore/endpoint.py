from .lso   import *
from typing import Any, Dict, Callable
import json
import threading
import time

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
    
    def request(self, route: str):
        """路由装饰器，用于注册处理不同路由的函数
        
        Args:
            route: 请求的路由名称
        """
        def decorator(func):
            self.routes[route] = func
            return func
        return decorator
    
    def default(self, func):
        """注册默认消息处理器，用于处理没有指定路由的消息
        
        Args:
            func: 处理函数
        """
        self.default_handler = func
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
                    print(f"处理响应 ID '{message_id}' 时出错: {e}")
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
                    print(f"处理路由 '{route}' 时出错: {e}")
            # 没有路由或路由未注册，使用默认处理器
            elif self.default_handler:
                try:
                    self.default_handler(data, info)
                except Exception as e:
                    print(f"默认处理器处理消息时出错: {e}")
    
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
        self.handler_thread = threading.Thread(target=self._handle_requests)
        self.handler_thread.daemon = True
        self.handler_thread.start()
        if block:
            self.handler_thread.join()
    def stop(self):
        """停止端点"""
        self.running = False
        if self.handler_thread:
            self.handler_thread.join(timeout=1.0)
        
        