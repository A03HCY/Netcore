# Netcore

[English](README_en.md) | 简体中文

Netcore 是一个轻量级且可扩展的通信框架，提供灵活的协议封装和通信管理机制。通过抽象传输层，它使开发者能够实现任何自定义通信方法，同时保持一致的接口。

## 特性

- 灵活的协议层
  - 可扩展的二进制协议
  - 支持 JSON 和原始数据格式
  - 可配置的大数据分块
  - 内存和文件存储选项

- 通用传输层
  - 抽象的传输接口
  - 异步数据传输
  - 自动消息队列
  - 支持任意自定义传输实现

- 错误处理
  - 标准日志系统
  - 异常管理
  - 数据完整性检查
  - 线程安全机制

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

# 创建通信管道和终端
pipe = Pipe(conn.recv, conn.send)
endpoint = Endpoint(pipe)

# 注册回声处理器
@endpoint.request('echo')
def handle_echo():
    message = request.json.get('message', '')
    return Response('echo', {"reply": f"服务器回声: {message}"})

# 注册默认处理器
@endpoint.default
def handle_default(data, info):
    endpoint.send_response({"status": "ok"}, info)

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

# 创建通信管道和终端
pipe = Pipe(client.recv, client.send)
endpoint = Endpoint(pipe)

# 注册消息处理器
@endpoint.request('echo')
def handle_echo():
    reply = request.json.get('reply', '')
    print(f"收到回声: {reply}")
    return None

# 启动客户端
endpoint.start(block=False)

# 发送消息
endpoint.send('echo', {"message": "Hello!"})
```

## 自定义传输示例

```python
# 定义自定义传输函数
def recv_func(size): 
    return your_device.read(size)
    
def send_func(data):
    your_device.write(data)

# 创建通信管道
pipe = Pipe(recv_func, send_func)

# 创建终端
endpoint = Endpoint(pipe)

# 注册路由处理器
@endpoint.route("echo")
def handle_echo():
    return Response("echo", request.data)

# 启动服务
endpoint.start()
```

## 文档

详细文档请访问 [https://netcore.acdp.top](https://netcore.acdp.top)

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。 