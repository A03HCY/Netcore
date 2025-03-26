from typing import Dict, List, Callable

import logging

logger = logging.getLogger("netcore.event")

class EventEmitter:
    """事件发射器，用于处理事件的订阅和触发"""
    
    def __init__(self):
        self._events: Dict[str, List[Callable]] = {}
        self._once_events: Dict[str, List[Callable]] = {}
    
    def on(self, event: str, handler: Callable):
        """订阅事件
        
        Args:
            event: 事件名称
            handler: 事件处理函数
        """
        if event not in self._events:
            self._events[event] = []
        self._events[event].append(handler)
        return self
    
    def once(self, event: str, handler: Callable):
        """订阅一次性事件
        
        Args:
            event: 事件名称
            handler: 事件处理函数
        """
        if event not in self._once_events:
            self._once_events[event] = []
        self._once_events[event].append(handler)
        return self
    
    def off(self, event: str, handler: Callable = None):
        """取消订阅事件
        
        Args:
            event: 事件名称
            handler: 可选的特定处理函数，如果不指定则移除所有处理函数
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
        """触发事件
        
        Args:
            event: 事件名称
            *args, **kwargs: 传递给处理函数的参数
        """
        # 处理普通事件
        if event in self._events:
            for handler in self._events[event]:
                try:
                    handler(*args, **kwargs)
                except Exception as e:
                    logger.error(f"事件 '{event}' 处理出错: {e}")
        
        # 处理一次性事件
        if event in self._once_events:
            handlers = self._once_events.pop(event)
            for handler in handlers:
                try:
                    handler(*args, **kwargs)
                except Exception as e:
                    logger.error(f"一次性事件 '{event}' 处理出错: {e}") 