# Netcore

Netcore 是一个轻量级的 Python 通信框架，提供简单易用类 Flask 风格的 API 用于构建通信应用。它支持基于路由的请求-响应模式，让通信就像调用本地函数一样简单。只要提供接收和发送函数，Netcore 就可以用于各种通信场景，包括网络 Socket、串口 UART、蓝牙等。

## 特性

- 简洁的 API 设计，降低通信编程复杂度
- 基于路由的请求-响应模式
- 支持异步通信和回调函数
- 自定义协议封装，确保数据传输可靠性
- 支持多种数据格式 (JSON, 字符串, 二进制数据)
- 内置工具类，提供实用功能
- **高度灵活性**，适用于各种通信方式 (Socket, UART, 蓝牙等)

## 安装

使用 pip 安装:

```bash
pip install netcore
```

## 快速开始

### 网络 Socket 示例

#### 服务器

```python
from netcore.lso import Pipe
from netcore.endpoint import Endpoint, Response, request
import socket

# 创建服务器
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('localhost', 8080))
server.listen(5)
print('服务器启动在端口 8080，等待客户端连接...')
conn, addr = server.accept()
print(f'客户端 {addr} 已连接')

# 创建Pipe和Endpoint
pipe = Pipe(conn.recv, conn.send)
endpoint = Endpoint(pipe)

# 注册路由处理函数
@endpoint.request('echo')
def handle_echo():
    message = request.json.get('message', '')
    print(f"收到echo请求: {message}")
    return Response('echo_reply', {"reply": f"服务器回声: {message}"})

# 启动Endpoint
endpoint.start(block=False)

# 主循环
try:
    while True:
        cmd = input("\n> ")
        if cmd.lower() == 'q':
            break
        
        # 向客户端发送消息
        endpoint.send('server_msg', {"text": cmd}, 
                     lambda data, info: print(f"收到响应: {data}"))
        
except KeyboardInterrupt:
    print("\n正在关闭...")
```

#### 客户端

```python
from netcore.lso import Pipe
from netcore.endpoint import Endpoint, Response, request
import socket

# 创建客户端
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('localhost', 8080))
print('已连接到服务器')

# 创建Pipe和Endpoint
pipe = Pipe(client.recv, client.send)
endpoint = Endpoint(pipe)

# 注册路由处理函数
@endpoint.request('server_msg')
def handle_server_msg():
    message = request.json.get('text', '')
    print(f"\n收到服务器消息: {message}")
    return Response('client_reply', {"status": "received"})

@endpoint.request('echo_reply')
def handle_echo_reply():
    reply = request.json.get('reply', '')
    print(f"\n收到回声响应: {reply}")
    return None

# 启动Endpoint
endpoint.start(block=False)

# 主循环
try:
    while True:
        cmd = input("\n> ")
        if cmd.lower() == 'q':
            break
            
        if cmd.startswith('echo '):
            message = cmd[5:]
            endpoint.send('echo', {"message": message}, 
                         lambda data, info: print(f"收到响应: {data}"))
        
except KeyboardInterrupt:
    print("\n正在关闭...")
```

### 串口 UART 示例

使用 Netcore 同样可以轻松实现串口通信：

```python
from netcore.lso import Pipe
from netcore.endpoint import Endpoint, Response, request
import serial

# 初始化串口
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)

# 定义接收和发送函数
def uart_recv(size=1):
    return ser.read(size)

def uart_send(data):
    ser.write(data)

# 创建Pipe和Endpoint
pipe = Pipe(uart_recv, uart_send)
endpoint = Endpoint(pipe)

# 注册路由处理函数
@endpoint.request('command')
def handle_command():
    cmd = request.json.get('cmd', '')
    print(f"收到命令: {cmd}")
    return Response('result', {"status": "success", "data": "命令已执行"})

# 启动Endpoint
endpoint.start(block=False)

# 主循环
try:
    while True:
        cmd = input("\n输入命令: ")
        if cmd.lower() == 'q':
            break
            
        endpoint.send('command', {"cmd": cmd}, 
                     lambda data, info: print(f"收到响应: {data}"))
        
except KeyboardInterrupt:
    print("\n正在关闭...")
finally:
    ser.close()
```

## 主要组件

### Pipe

`Pipe` 是底层通信管道，负责数据的发送和接收。只要提供合适的接收和发送函数，它就可以适用于任何通信方式。

```python
# Socket通信
pipe = Pipe(socket.recv, socket.send)

# 串口通信
pipe = Pipe(serial.read, serial.write)

# 自定义通信
pipe = Pipe(my_custom_recv_func, my_custom_send_func)

# 启动通信管道
pipe.start()
```

### Endpoint

`Endpoint` 是高级API，建立在 `Pipe` 之上，提供了基于路由的请求-响应模式。

```python
# 创建Endpoint实例
endpoint = Endpoint(pipe)
endpoint.start()  # 启动端点

# 注册路由处理函数
@endpoint.request('route_name')
def handle_request():
    # 处理请求
    return Response('response_route', data)

# 发送请求
endpoint.send('route_name', data, callback_function)

# 发送响应
endpoint.send_response(data, info)
```

### Utils

`Utils` 类提供了一系列实用的静态方法，如数据格式化、数据分割、安全码生成等。

```python
# 格式化字节大小
Utils.bytes_format(1500)  # '1.46 KB'

# 生成安全码
Utils.safe_code(8)  # 生成8字符的随机安全码

# 分割数据
chunks = Utils.split_bytes_into_chunks(data, 1024)
```

## API文档

### Request 对象

全局的 `request` 对象用于在处理请求时访问请求数据：

- `request.meta` - 原始请求数据（字节格式）
- `request.json` - 请求数据解析为JSON对象（如果可能）
- `request.string` - 请求数据解析为字符串（如果可能）

### Response 类

`Response` 类用于创建响应对象：

```python
# 创建一个响应
response = Response('route_name', data)
```

### Endpoint 类方法

- `start()` - 启动端点
- `stop()` - 停止端点
- `request(route)` - 路由装饰器，用于注册处理函数
- `default(func)` - 默认处理器装饰器，处理未注册路由的请求
- `send(route, data, callback)` - 发送请求
- `send_response(data, info)` - 发送响应

## 许可证

MIT 许可证 