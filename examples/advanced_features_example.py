from netcore.endpoint import Endpoint, Response, request
from netcore.lso import Pipe
import time
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG)

# 创建管道和端点
pipe = Pipe(lambda size: b'', lambda data: None)
endpoint = Endpoint(pipe)

# 使用事件系统
@endpoint.event.on('start')
def on_start():
    print("端点启动")

@endpoint.event.on('request')
def on_request(data, info):
    print(f"收到请求: {info}")

# 使用定时任务
def periodic_task():
    print(f"执行定时任务: {time.strftime('%H:%M:%S')}")

endpoint.scheduler.schedule(periodic_task, delay=0, interval=5)  # 每5秒执行一次

# 使用缓存系统
@endpoint.request("/cached-data")
def get_cached_data():
    # 先尝试从缓存获取
    data = endpoint.cache.get("expensive_data")
    if data is None:
        # 模拟耗时操作
        time.sleep(1)
        data = {"timestamp": time.time(), "value": "expensive computation result"}
        # 缓存结果，有效期10秒
        endpoint.cache.set("expensive_data", data, ttl=10)
    return Response("/cached-data", data)

# 启动端点
endpoint.start() 