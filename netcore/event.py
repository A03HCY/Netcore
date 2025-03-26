from typing import Dict, List, Callable

import logging

logger = logging.getLogger("netcore.event")

class EventEmitter:
    """Event emitter for handling event subscription and triggering"""
    
    def __init__(self):
        self._events: Dict[str, List[Callable]] = {}
        self._once_events: Dict[str, List[Callable]] = {}
    
    def on(self, event: str, handler: Callable = None):
        """Subscribe to an event
        
        Args:
            event: Event name
            handler: Event handler function, if None then used as decorator
            
        Returns:
            handler or decorator function
        """
        # 如果没有提供handler，返回一个装饰器函数
        if handler is None:
            def decorator(func):
                if event not in self._events:
                    self._events[event] = []
                self._events[event].append(func)
                return func
            return decorator
        
        # 常规调用方式
        if event not in self._events:
            self._events[event] = []
        self._events[event].append(handler)
        return self
    
    def once(self, event: str, handler: Callable = None):
        """Subscribe to a one-time event
        
        Args:
            event: Event name
            handler: Event handler function, if None then used as decorator
            
        Returns:
            handler or decorator function
        """
        # 如果没有提供handler，返回一个装饰器函数
        if handler is None:
            def decorator(func):
                if event not in self._once_events:
                    self._once_events[event] = []
                self._once_events[event].append(func)
                return func
            return decorator
        
        # 常规调用方式
        if event not in self._once_events:
            self._once_events[event] = []
        self._once_events[event].append(handler)
        return self
    
    def off(self, event: str, handler: Callable = None):
        """Unsubscribe from an event
        
        Args:
            event: Event name
            handler: Optional specific handler to remove, if not specified removes all handlers
        """
        if handler is None:
            self._events.pop(event, None)
            self._once_events.pop(event, None)
        else:
            if event in self._events:
                self._events[event] = [h for h in self._events[event] if h != handler]
            if event in self._once_events:
                self._once_events[event] = [h for h in self._once_events[event] if h != handler]
        return self
    
    def emit(self, event: str, *args, **kwargs):
        """Trigger an event
        
        Args:
            event: Event name
            *args, **kwargs: Parameters to pass to the handler functions
        """
        # 处理普通事件
        if event in self._events:
            for handler in self._events[event]:
                try:
                    handler(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error processing event '{event}': {e}")
        
        # 处理一次性事件
        if event in self._once_events:
            handlers = self._once_events.pop(event)
            for handler in handlers:
                try:
                    handler(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error processing one-time event '{event}': {e}") 