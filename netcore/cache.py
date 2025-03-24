from typing import Any, Optional, Dict
import time
import threading
import logging

logger = logging.getLogger("netcore.cache")

class Cache:
    """简单的内存缓存系统"""
    
    def __init__(self, default_ttl: int = 300):
        """初始化缓存
        
        Args:
            default_ttl: 默认的缓存生存时间（秒）
        """
        self._cache: Dict[str, tuple[Any, float, Optional[int]]] = {}  # (value, timestamp, ttl)
        self._default_ttl = default_ttl
        self._lock = threading.Lock()
        
        # 启动清理线程
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop)
        self._cleanup_thread.daemon = True
        self._cleanup_thread.start()
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 可选的生存时间（秒）
        """
        with self._lock:
            self._cache[key] = (value, time.time(), ttl or self._default_ttl)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值
        
        Args:
            key: 缓存键
            default: 键不存在时返回的默认值
            
        Returns:
            缓存的值或默认值
        """
        with self._lock:
            if key not in self._cache:
                return default
            
            value, timestamp, ttl = self._cache[key]
            if time.time() - timestamp > ttl:
                del self._cache[key]
                return default
            
            return value
    
    def delete(self, key: str):
        """删除缓存项
        
        Args:
            key: 要删除的缓存键
        """
        with self._lock:
            self._cache.pop(key, None)
    
    def clear(self):
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
    
    def _cleanup_loop(self):
        """清理过期缓存的循环"""
        while True:
            time.sleep(60)  # 每分钟检查一次
            with self._lock:
                now = time.time()
                expired = [
                    key for key, (_, timestamp, ttl) in self._cache.items()
                    if now - timestamp > ttl
                ]
                for key in expired:
                    del self._cache[key] 