from typing import Any, Optional, Dict

import time
import threading
import logging

logger = logging.getLogger("netcore.cache")

class Cache:
    """Simple in-memory cache system"""
    
    def __init__(self, default_ttl: int = 300):
        """Initialize cache
        
        Args:
            default_ttl: Default time-to-live for cached items (seconds)
        """
        self._cache: Dict[str, tuple[Any, float, Optional[int]]] = {}  # (value, timestamp, ttl)
        self._default_ttl = default_ttl
        self._lock = threading.Lock()
        
        # 启动清理线程
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop)
        self._cleanup_thread.daemon = True
        self._cleanup_thread.start()
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set cache value
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional time-to-live (seconds)
        """
        with self._lock:
            self._cache[key] = (value, time.time(), ttl or self._default_ttl)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get cached value
        
        Args:
            key: Cache key
            default: Default value to return if key doesn't exist
            
        Returns:
            Cached value or default
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
        """Delete cache item
        
        Args:
            key: Cache key to delete
        """
        with self._lock:
            self._cache.pop(key, None)
    
    def clear(self):
        """Clear all cached items"""
        with self._lock:
            self._cache.clear()
    
    def _cleanup_loop(self):
        """Cleanup loop for expired cache items"""
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