from typing import Dict, Callable, Any, Optional, List
import logging
import functools

# 配置日志记录器
logger = logging.getLogger("netcore.blueprint")

class Blueprint:
    """蓝图类，用于组织路由和处理函数
    
    蓝图可以定义一组路由和相应的处理函数，并在注册到Endpoint时添加前缀。
    这样可以更好地组织大型应用的代码，将相关功能分组。
    """
    
    def __init__(self, name: str, prefix: str = ""):
        """创建蓝图
        
        Args:
            name: 蓝图名称，用于标识和日志
            prefix: 路由前缀，会添加到所有路由前面
        """
        self.name = name
        self.prefix = prefix
        self.routes: Dict[str, Callable] = {}
        self.middlewares: List[Callable] = []  # 蓝图中间件列表
        self.error_handler = None  # 蓝图错误处理器
        self.before_request_funcs: List[Callable] = []  # 请求前钩子
        self.after_request_funcs: List[Callable] = []  # 请求后钩子
        logger.info(f"创建蓝图 '{name}' 前缀为 '{prefix}'")
    
    def request(self, route: str):
        """路由装饰器，用于注册处理不同路由的函数
        
        与Endpoint.request保持一致的命名和使用方式
        
        Args:
            route: 不包含前缀的路由路径
            
        Returns:
            装饰器函数
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
            
            full_route = f"{self.prefix}{route}"
            self.routes[full_route] = wrapper
            logger.debug(f"蓝图 '{self.name}' 注册路由 '{full_route}'")
            return func
        return decorator 

    def middleware(self, func):
        """中间件装饰器
        
        Args:
            func: 中间件函数，接收handler作为参数，返回新的handler
        """
        self.middlewares.append(func)
        logger.debug(f"蓝图 '{self.name}' 添加中间件 '{func.__name__}'")
        return func
    
    def error_handle(self, func):
        """错误处理装饰器
        
        Args:
            func: 错误处理函数，接收异常作为参数
        """
        self.error_handler = func
        logger.debug(f"蓝图 '{self.name}' 设置错误处理器 '{func.__name__}'")
        return func
    
    def before_request(self, func):
        """请求前钩子装饰器
        
        Args:
            func: 在请求处理前执行的函数
        """
        self.before_request_funcs.append(func)
        logger.debug(f"蓝图 '{self.name}' 添加请求前钩子 '{func.__name__}'")
        return func
    
    def after_request(self, func):
        """请求后钩子装饰器
        
        Args:
            func: 在请求处理后执行的函数，接收响应对象作为参数
        """
        self.after_request_funcs.append(func)
        logger.debug(f"蓝图 '{self.name}' 添加请求后钩子 '{func.__name__}'")
        return func
    
    def default(self, func):
        """注册默认处理器
        
        为保持与Endpoint风格一致
        
        Args:
            func: 默认处理函数
        """
        full_route = f"{self.prefix}/__default__"
        self.routes[full_route] = func
        logger.debug(f"蓝图 '{self.name}' 设置默认处理器 '{func.__name__}'")
        return func 