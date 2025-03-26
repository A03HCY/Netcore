from typing   import Callable, Optional
from datetime import datetime, timedelta

import threading
import time
import logging
import heapq

logger = logging.getLogger("netcore.scheduler")

class Scheduler:
    """Task scheduler for timed task execution.
    
    Manages scheduled tasks with support for one-time delayed execution
    and periodic recurring tasks.
    """
    
    def __init__(self):
        self._tasks = []  # 优先队列
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
    
    def _run(self):
        """Run the scheduler main loop.
        
        Continuously checks for tasks that need to be executed based on their
        scheduled time and handles recurring tasks.
        """
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
                        logger.error(f"Error executing scheduled task: {e}")
            
            time.sleep(0.1)  # 避免过度占用CPU
    
    def start(self):
        """Start the scheduler.
        
        Begins the scheduler thread if it's not already running.
        Returns immediately without waiting for task execution.
        """
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run)
        self._thread.daemon = True
        self._thread.start()
    
    def stop(self):
        """Stop the scheduler.
        
        Stops task execution and waits for the scheduler thread to terminate.
        """
        self._running = False
        if self._thread:
            self._thread.join()
    
    def schedule(self, task: Callable, delay: float = 0, interval: Optional[float] = None):
        """Schedule a task for execution.
        
        Args:
            task: Function to execute
            delay: Initial delay in seconds before first execution
            interval: If specified, the task will repeat every interval seconds
        
        The task will be executed after the specified delay. If an interval
        is provided, the task will continue to run periodically.
        """
        with self._lock:
            next_time = datetime.now() + timedelta(seconds=delay)
            heapq.heappush(self._tasks, (next_time, task, interval)) 