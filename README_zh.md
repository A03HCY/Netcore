# Netcore

[![status](https://joss.theoj.org/papers/08b1c73b184c1341f51e01ee052647ae/status.svg)](https://joss.theoj.org/papers/08b1c73b184c1341f51e01ee052647ae) ![PyPI - Version](https://img.shields.io/pypi/v/netcore?label=PyPI&color=green)

[English](README.md) | 简体中文

Netcore 是一个轻量级通信框架，实现了单一连接中的并发消息传输。通过实现类似 CPU 时间片分割的消息分块和调度机制，它允许在不建立多个连接的情况下同时发送和接收多个消息。

## 核心特性

- 并发消息传输
  - 单一连接处理多个并发消息
  - 自动消息分块与重组
  - 消息调度与优先级处理
  - 非阻塞消息传输

- 智能消息管理
  - 唯一消息ID追踪
  - 自动消息队列
  - 消息优先级处理
  - 消息完整性验证

- 协议层
  - 支持消息分块的二进制协议
  - 支持 JSON 和原始数据格式
  - 可配置的分块大小
  - 内存和文件存储选项

- 传输层抽象
  - 通用传输接口
  - 异步数据传输
  - 线程安全机制
  - 支持自定义传输实现

## 高级功能

- 蓝图系统
  - 路由分组和前缀
  - 模块化应用结构
  - 蓝图级别的中间件支持
  - 独立的错误处理机制

- 事件系统
  - 事件订阅和发布
  - 一次性事件处理
  - 系统事件监控
  - 异步事件处理

- 任务调度器
  - 延迟任务执行
  - 周期性任务调度
  - 基于优先级的调度
  - 线程安全的任务管理

- 缓存系统
  - 内存缓存
  - TTL（生存时间）支持
  - 自动缓存清理
  - 线程安全操作

## 安装

使用 pip 安装:

```bash
pip install netcore
```

## 快速开始

### 服务器示例

```python
from netcore import Endpoint, Pipe, Response, request
import socket

# 创建 TCP 服务器
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('localhost', 8080))
server.listen(5)
conn, addr = server.accept()

# 创建管道和终端
pipe = Pipe(conn.recv, conn.send)
endpoint = Endpoint(pipe)

# 注册并发消息处理器
@endpoint.request('message1')
def handle_message1():
    # 此处理器可以在处理其他消息的同时运行
    return Response('message1', {"status": "已处理"})

@endpoint.request('message2')
def handle_message2():
    # 另一个并发处理器
    return Response('message2', {"status": "已处理"})

# 启动服务
endpoint.start()
```

### 客户端示例

```python
from netcore import Endpoint, Pipe, Response, request
import socket

# 连接到服务器
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('localhost', 8080))

# 创建管道和终端
pipe = Pipe(client.recv, client.send)
endpoint = Endpoint(pipe)

# 启动客户端（非阻塞）
endpoint.start(block=False)

# 并发发送多个消息
endpoint.send('message1', {"data": "第一条消息"})
endpoint.send('message2', {"data": "第二条消息"})
# 两条消息将被并发处理
```

## 高级用法示例

### 蓝图示例
```python
from netcore import Endpoint, Blueprint, Response, request

# 创建用户相关路由的蓝图
user_bp = Blueprint("users", "/user")

@user_bp.request("/list")
def user_list():
    return Response("/user/list", {"users": ["用户1", "用户2"]})

# 注册蓝图到端点
endpoint.register_blueprint(user_bp)
```

### 事件系统示例
```python
# 订阅事件
@endpoint.event.on('start')
def on_start():
    print("服务已启动")

# 一次性事件
@endpoint.event.once('initialize')
def on_init():
    print("首次初始化")

# 触发事件
endpoint.event.emit('custom_event', data={"type": "通知"})
```

### 任务调度器示例
```python
# 调度周期性任务
def periodic_check():
    print("执行周期性检查")

endpoint.scheduler.schedule(periodic_check, delay=5, interval=60)  # 5秒后开始，每60秒执行一次
```

### 缓存系统示例
```python
# 缓存耗时操作
@endpoint.request('/data')
def get_data():
    # 尝试从缓存获取
    data = endpoint.cache.get("expensive_data")
    if data is None:
        # 计算并缓存5分钟
        data = compute_expensive_data()
        endpoint.cache.set("expensive_data", data, ttl=300)
    return Response("/data", data)
```

## 工作原理

1. **消息分块**: 大消息自动分割成小块
2. **并发处理**: 每个消息独立处理
3. **调度机制**: 不同消息的块交错传输以提高效率
4. **自动重组**: 消息块在目标端自动重组

## 文档

详细文档请访问 [https://netcore.acdp.top](https://netcore.acdp.top)

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。 