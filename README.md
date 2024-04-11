# Netcore

一个用于简化数据传输流程的库。传输中，它能解决流传输粘包、数据丢失等问题，支持原格式传输；功能开发上，它使用类Flask框架拓展业务，无需写繁琐的条件判断，对项目有良好的可维护性。

[TOC]

## 安装

Netcore 已上传至 PYPI 与 Github，使用以下其一命令即可快速安装。

```bash
pip install netcore
pip install git+https://github.com/A03HCY/Netcore.git
```

你也可以通过 git clone 进行源码安装。

```bash
git clone https://github.com/A03HCY/Netcore.git
cd Netcore
python setup.py install
```

## 使用

### Protocol

#### 快速使用

通过 Protocol 收发数据。

```python
from netcore import protocol as pt
from rich    import print
import io

pool = io.BytesIO()

# ==========
data = pt.Protocol(extension='.example')
data.upmeta({
    'msg': [1, 2, 3]
})
data.create_stream(pool.write)
# ==========

pool.seek(0)

# ==========
recv = pt.Protocol()
recv.load_stream(pool.read)
# ==========

print('[blue]Extn:', recv.extn)
print('[blue]Json:', recv.json)

'''
Extn: .example
Json:
{'msg': [1, 2, 3]}
'''
```

Protocol 支持链式调用。

```python
# 发送数据
data = pt.Protocol(extension='.this_is_extn').upmeta({
    'msg': [1, 2, 3]
}).create_stream(sender)

# 接收数据
recv = pt.Protocol().load_stream(recver)
```

#### 详细

Netcore 提供它的核心协议以在某些方面（ 如与微控制器通信 ）节省宽带。

```python
def __init__(self, meta:bytes=b'', extension:str='', encoding:str='utf-8', buff:int=2048) -> None:...
```

|   字段    |           说明           |
| :-------: | :----------------------: |
|   meta    |        包含的数据        |
| extension | 标识，如同文件扩展名一样 |
| encoding  |       编码解码方式       |
|   buff    |   发送数据的缓冲区大小   |

```python
def upmeta(self, data):...
```

用于更新meta，此处data类型若为内置类型，则接收方收到的数据为该类型。

```python
@property
def code(self) -> str:...
```

此函数会尝试将meta解码成字符串。

```python
@property
def json(self) -> dict:...
```

此函数会尝试将meta解码成字典。

```python
@property
def pack(self) -> bytes:...
```

此函数会返回完整的协议数据。

```python
def write(self, data:bytes):...

def read(self, length:int=None) -> bytes:...

def seek(self, location:int):...
```

用于模拟文件读写。

```python
def load_stream(self, func, from_head:tuple=None):...
```

此函数会尝试从一个能够接受数据的 func 按照规定好的协议获取数据，并覆盖实例。

```python
def create_stream(self, func):...
```

此函数会将数据传入 func。

### Package

这个类对 Protocol 进行了封装，它支持：

- 检查数据完整性。
- 将多个 Protocol 拆分成小段发送。
- 返回进度信息。
- 自定义错误处理函数。

#### 快速使用

此类通过多线程对数据传输实时监听，因此使用 socket 演示。

```python
from netcore import protocol as pt
from rich    import print
import socket

inp = input('mode[s/c]:')

if inp == 's':
    print('[blue]Server mode')
    sk = socket.socket()
    sk.bind(('0.0.0.0', 5555))
    sk.listen()
    conn, addr = sk.accept()

    print('[green]Connected')
    pk = pt.Package(sender=conn.send, recver=conn.recv, buff=2048)
    pk.start()

    while True:
        data = pk.recv()
        print('Recv:', data)

elif inp == 'c':
    print('[blue]Client mode')
    sk = socket.socket()
    sk.connect(('localhost', 5555))
    pk = pt.Package(sender=sk.send, recver=sk.recv, buff=2048)
    pk.start()

    while True:
        msg = input('msg# ')
        pk.send(msg)
```

#### 详细

```python
def __init__(self, sender, recver, buff:int=2048):...
```

|  字段  |        说明        |
| :----: | :----------------: |
| sender | 用于发送数据的函数 |
| recver | 用于获取数据的函数 |
|  buff  |   数据拆分的大小   |

```python
def start(self):...

def close(self):...
```

用于启动或终止服务。

```python
def send(self, data):...
```

发送数据，data 可以为内置类型或 Protocol。

```python
def recv(self):...
```

接收数据。

```python
def error(self, func):...
```

自定义异常处理，func 需要接收一个字符串参数，该字符串用于反应出错位置。

| 数据 |       含义       |
| :--: | :--------------: |
| send | 在发送数据时出错 |
| recv | 在接收数据时出错 |

两者一般是在连接断开时触发。

### Endpoint

使用类似 Flask 的方式对你的业务进行搭建。

#### 快速使用

```pascal
from netcore import endpoint as ep
from rich    import print
import socket

inp = input('mode[s/c]:')

if inp == 's':
    sk = socket.socket()
    sk.bind(('0.0.0.0', 6666))
    sk.listen()
    conn, addr = sk.accept()
    
    # ==========
    end = ep.Endpoint(conn.send, conn.recv) 

    @end.route('.say')
    def say(data:ep.Request):
        print(data.code)
        data.response('.res', 'recved')

    end.start()
    # ==========

    conn.close()
    sk.close()

elif inp == 'c':
    sk = socket.socket()           
    sk.connect(('127.0.0.1', 6666))

    # ==========
    pk = ep.Endpoint(sk.send, sk.recv, buff=2048)

    @pk.route('.res')
    def res(data:ep.Request):
        print(data.code)

    pk.start(thread=True)
    # ==========

    while True:
        msg = input('> ')
        if msg == 'exit': break
        pk.send(ep.Protocol(extension='.say', meta=msg.encode('utf-8')))

    pk.close()
    sk.close()
```

