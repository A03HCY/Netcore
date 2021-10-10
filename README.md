# Network Core

**项目正在重构，需要较为完善的功能可以转到 [release](https://gitee.com/intellen/network/tree/release/) 分支中查看 v0.1.1 版本。**

起初我在做一些有关于网络通信的程序时，遇到了两台设备在不同网段（不同局域网）的情况，而网上的一些方案对于我来说懒得用 [doge] ，而且也想用 Python 实现这一功能，于是这个小项目诞生了。

由于是一个人开发，有些文档，注释或示例都没有及时更新，有些 bug 也不能及时发现，所以欢迎大家提交 Issues 和 Pull Requests 。

💡 IPv6 已经考虑，可能会在以后的版本中支持。

##  项目结构

```wiki
Intellen Network Core
├── SDK.py      # 客户端
├── Service.py  # 服务端
├── Ucode.py    # 共用函数
```

##  ☁️ 快速开始

请确保你已经安装了 Python 3 ，由于这是一个轻量级的项目，在运行核心程序时无需安装任何额外的库，但当你需要运行扩展程序时，请先安装可能需要的依赖库。

```shell
# pip install acdpnet 仅停留在 v0.1.1 版本，迭代到 v1.0.5 会进行更新

# 扩展程序不需要其他第三方库
```

### 服务端

在一台拥有公网 IP 的服务器上运行以下代码（当然如果你只是想将它用在局域网内是可以的）。

```python
import Service as ns

ns.PASS_WORD = '123456'  # 用于修改连接密码
ns.PASS_PORT = 1305      # 用于修改端口

ns.start()               # 启动服务
```

💡 之后会公布用于测试的免费服务地址。

### 客户端

#### 创建一个连接

**Toconer()** 此类 class 够帮助我们建立一个完整流程，下面演示一个完整的连接所需要的全部内容。你可以自行在其中添加更多代码，来构建一个应用。

```python
from SDK import *

host = "link.acdp.top" # 服务器地址，暂时仅支持 IPv4 地址
port = 1305            # 服务端口
pwd = "123456"         # 这是登录服务器需要的密码

Tocon = Toconer((host, port), pwd) # 连接

# 在这里写上你的代码

Tocon.close() # 主动断开连接
```

**Tocon.reset()** 在网络因各种因素断开需要再次连接使用 。

#### 发送与接收消息

**Tocon.listnodes()** 此函数可以帮助我们列出当前在线的设备，在发送消息之前，我们首先要知道对方的 UID 。

```python
nodes_list = Tocon.listnodes()
print('nodes_list =', nodes_list)
```

```python
# ---------- 打印结果
nodes_list = [{'uid': '1qagyp4m7e-y7t-7xh1o', 'name': 'Corty', 'platform': 'Windows-10-10.0.19041-SP0'}]

# ---------- 内容解释
nodes_list = [
    { # 第一个设备
        'uid':'设备的 UID',
        'name':'设备的名称',
        'platform':'设备的操作系统以及版本号'
    },
    { # 第二个设备
        '...'
    }
]
```

**Tocon.send()** 用来发送一条数据，其中 data 可以是以下类型的数据。

```python
# 目标设备的 UID
uid = '1qagyp4m7e-y7t-7xh1o'
# 数据类型可以是: str, list, dict, tuple, bytes.
data = 'Hi Friend.'

Tocon.send(data, uid)
```

**Tocon.recv()** 用来接收一条数据。

```python
msg = Tocon.recv()
print('msg =', msg)
```

```python
# ---------- 打印结果
msg = ('Hi Friend.', {'time': 1633100215.2722294, 'sender': '1qagyp4m7e-y7t-7xh1o'})

# ---------- 内容解释
msg = (
    'Hi Friend.', # 发送过来的消息
    {
     'time': 1633100215.2722294,      # 服务器接收到的时间
     'sender': '1qagyp4m7e-y7t-7xh1o' # 发送者的 UID
    }
)
```

#### 远程操作

