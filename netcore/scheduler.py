from typing   import Callable, Optional
from datetime import datetime, timedelta

import threading
import time
import logging
import heapq

logger = logging.getLogger("netcore.scheduler")

class Scheduler:
    """定时任务调度器"""
    
    def __init__(self):
        self._tasks = []  # 优先队列
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
    
    def _run(self):
        """运行调度器主循环"""
        while self._running:
            with self._lock:
                now = datetime.now()
                while self._tasks and self._tasks[0][0] <= now:
                    _, task, interval = heapq.heappop(self._tasks)
                    try:
                        task()
                        if interval:  # 如果是周期性任务，重新加入队列
                            next_time = now + timedelta(seconds=interval)
                            heapq.heappush(self._tasks, (next_time, task, interval))
                    except Exception as e:
                        logger.error(f"执行定时任务出错: {e}")
            
            time.sleep(0.1)  # 避免过度占用CPU
    
    def start(self):
        """启动调度器"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run)
        self._thread.daemon = True
        self._thread.start()
    
    def stop(self):
        """停止调度器"""
        self._running = False
        if self._thread:
            self._thread.join()
    
    def schedule(self, task: Callable, delay: float = 0, interval: Optional[float] = None):
        """调度任务
        
        Args:
            task: 要执行的任务函数
            delay: 延迟执行的秒数
            interval: 如果指定，任务将每隔interval秒执行一次
        """
        with self._lock:
            next_time = datetime.now() + timedelta(seconds=delay)
            heapq.heappush(self._tasks, (next_time, task, interval)) 