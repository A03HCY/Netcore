# Network Core

一个能够用简洁的方式来构建通信服务的轻量级框架。

## 方法

此项目已上传 [acdpnet · PyPI](https://pypi.org/project/acdpnet/) ，快速安装可使用以下命令。

```shell
pip install acdpnet -i https://pypi.org/simple
```

### 构建服务

#### 基本框架

```python
from acdpnet import services

app = services.Tree()

# extension

app.run(('0.0.0.0', 1035), token='ASDF')
```

通过以上代码可以快速构建一个服务端，但仍然**无法投入使用**，在此之上还需要加上用户认证的功能。

#### 用户认证

##### 简单的用户创建方式

```python
app.idf.acessuid = {
    'Name':'Password'
}
```

##### 自定义用户认证

```python
class Login(services.Idenfaction):
    def setup(self):
        pass
    
    def Idenfy(self, account:str, key:str):
        if key == self.acessuid.get(account):
            return True
        else:
            return False

app.idf = Login()
```

#### 服务拓展

完成了基本的框架后，就可以为服务端添加功能啦。

##### 通过函数拓展

```python
from acdpnet.tools import Conet
# 引用此类是为了在写代码时出现代码提示，可不引用

@app.command('command_name')
def Dosomething(conet:Conet):
    pass
```

##### 通过类拓展

```python
from acdpnet.tools import Conet

class Serv:
    @staticmethod
    def command_name_1(conet:Conet):
    	pass
    
    @staticmethod
    def command_name_2(conet:Conet):
    	pass

app.extension(Serv)
```

##### 通过内置拓展添加

此库中内置了一些预先写好的拓展，可以通过以下方式添加。

```python
from acdpnet.extension import transfer

app.extension(transfer.Transfer)
```

### 构建客户端

#### 基本方式

```python
from acdpnet import nodes

app = nodes.BasicNode('Name', 'Password')
app.connect(('localhost', 1035), token='ASDF')

# do something

app.close()
```

#### 发送与接收

##### 发送命令及数据

```python
data = {
    ...
}
app.send('Your command', data)
```

##### 接收命令与数据

```python
resp = app.recv()
# 由服务端决定返回 dict 或 list
```

## 内置扩展

### 服务端

#### extension.transfer.InfoSupport

支持查询所有在线的客户端信息，使用 **activities** 命令。

#### extension.transfer.TransferSupport

```python
description = {
    'trans':{
        'desc':'Send data from a node to another one',
        'args':[{
            'remote':'Type:String Desc:Target Mac'
        }],
        'resp':''
    },
    'multi_cmd':{
        'desc':'Send a command from a node to another one',
        'args':[{
            'remote':'Type:String Desc:Target Mac',
            'command':'Type:String Desc:Command to execute',
        }],
        'resp':'Unknow'
    },
    'flow_trans':{
        'desc':'TCP flow',
        'args':[{
            'remote':'Type:String Desc:Target Mac',
        }],
        'resp':'Unknow'
    },
}
```

##### **trans** 命令

支持客户端互相发送消息，必要参数 remote:str 用于指定目标，需通过 InfoSupport 获取。

##### **multi_cmd** 命令

用于客户端之间的命令操作，必要参数 remote:str, command:str

##### **flow_trans** 命令

以数据流的形式转发数据，可用于大文件转发，，必要参数 remote:str 用于指定目标

### 客户端

#### extension.transfer.FilesNodes

```python
description = {
    'ls':{
        'desc':'Remote list a path info',
        'args':[{}],
        'resp':'Type:Dict'
    },
    'cd':{
        'desc':'Change work dir',
        'args':[{
            'path':'Type:String Target path'
        }],
        'resp':'Type:Dict'
    },
    'pwd':{
        'desc':'Get work dir',
        'args':[{}],
        'resp':'Type:Dict'
    },
    'rm':{
        'desc':'Remove a file',
        'args':[{
            'name':'Type:String Target file'
        }],
        'resp':'Type:Dict'
    },
    'rmdir':{
        'desc':'Remove a dir',
        'args':[{
            'path':'Type:String Target path'
        }],
        'resp':'Type:Dict'
    },
    'search':{
        'desc':'Search a file',
        'args':[{
            'key':'Type:String Target file keyword'
        }],
        'resp':'Type:Dict'
    },
    'get':{
        'desc':'Get remote file by flow_trans',
        'args':[{
            'name':'Type:String filename at pwd'
        }],
        'resp':'Type:Dict'
    },
    'fileraw':{
        'desc':'Read / Write raw data',
        'args':[{
            'path':'Type:String filename at pwd',
            'mode':'Type:String mode',
            'seek':'Type:Int',
            'buff':'Type:Int',
            'raw_':'write mode, raw data'
        }],
        'resp':'Type:Dict'
    },
}
```

仅应用于被控客户端，即使用 ExtensionSupportNode 来创建客户端，此客户端功能拓展方式与服务端一致。

此拓展实现了简单的远程文件操作功能，详细命令与参数参考以上解释或查看源码。

#### extension.transfer.RemoteFileSystem

类似于 os 库，其中仿写了 open() 函数，可打开远程客户端的文件。

#### extension.automatic.ScreenNodes

仅应用于被控客户端，访问屏幕数据。

#### extension.automatic.RemoteScreen

```python
class RemoteScreen(RemoteExtension):
    def show(self):...
```

直接调用 show 方法将展示远程客户端的电脑截图，使用本机默认的图片查看器。

使用此拓展需要远程被控端添加 extension.automatic.ScreenNodes

## 内置工具

### tools.RemoteGet

```python
class RemoteGet:
    def __init__(self, conet:Conet):...
    
    def To(self, f) -> self:...

    def Now(self, func=None):...

    def Now_Progress(self, console):...
```

在执行获取从远程客户端下载文件命令后，可使用本工具用来简化接受流程，

### tools.RemotePush

```python
class RemoteGet:
    def __init__(self, conet:Conet):...
    
    def To(self, f) -> self:...

    def Now(self, func=None):...

    def Now_Progress(self, console):...
```

在执行推送文件至远程端后，可使用本工具用来简化发送流程，
