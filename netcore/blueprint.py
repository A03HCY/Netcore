from typing import Dict, Callable, List

import logging
import functools

# 配置日志记录器
logger = logging.getLogger("netcore.blueprint")

class Blueprint:
    """Blueprint class, used to organize routes and handler functions.
    
    A blueprint can define a group of routes and corresponding handlers, 
    and add a prefix when registered to an Endpoint.
    This allows better organization of code in large applications by 
    grouping related functionality.
    """
    
    def __init__(self, name: str, prefix: str = ""):
        """Create a blueprint.
        
        Args:
            name: Blueprint name, used for identification and logging
            prefix: Route prefix, will be added to all routes
        """
        self.name = name
        self.prefix = prefix
        self.routes: Dict[str, Callable] = {}
        self.middlewares: List[Callable] = []  # 蓝图中间件列表
        self.error_handler = None  # 蓝图错误处理器
        self.before_request_funcs: List[Callable] = []  # 请求前钩子
        self.after_request_funcs: List[Callable] = []  # 请求后钩子
        logger.info(f"Created blueprint '{name}' with prefix '{prefix}'")
    
    def request(self, route: str):
        """Route decorator, used to register functions for handling different routes.
        
        Simply stores the handler function with its route in the routes dictionary.
        The actual wrapping will be done when registered to an Endpoint.
        
        Args:
            route: Route path without prefix
            
        Returns:
            Decorator function
        """
        def decorator(func):
            full_route = f"{self.prefix}{route}"
            self.routes[full_route] = func
            logger.debug(f"Blueprint '{self.name}' registered route '{full_route}'")
            return func
        return decorator

    def middleware(self, func):
        """Middleware decorator.
        
        Args:
            func: Middleware function that accepts a handler as parameter and returns a new handler
        """
        self.middlewares.append(func)
        logger.debug(f"Blueprint '{self.name}' added middleware '{func.__name__}'")
        return func
    
    def error_handle(self, func):
        """Error handler decorator.
        
        Args:
            func: Error handling function that accepts an exception as parameter
        """
        self.error_handler = func
        logger.debug(f"Blueprint '{self.name}' set error handler '{func.__name__}'")
        return func
    
    def before_request(self, func):
        """Before request hook decorator.
        
        Args:
            func: Function to execute before request processing
        """
        self.before_request_funcs.append(func)
        logger.debug(f"Blueprint '{self.name}' added before request hook '{func.__name__}'")
        return func
    
    def after_request(self, func):
        """After request hook decorator.
        
        Args:
            func: Function to execute after request processing, receives response object as parameter
        """
        self.after_request_funcs.append(func)
        logger.debug(f"Blueprint '{self.name}' added after request hook '{func.__name__}'")
        return func
    
    def default(self, func):
        """Register default handler.
        
        Maintains consistency with Endpoint style
        
        Args:
            func: Default handler function
        """
        full_route = f"{self.prefix}/__default__"
        self.routes[full_route] = func
        logger.debug(f"Blueprint '{self.name}' set default handler '{func.__name__}'")
        return func 