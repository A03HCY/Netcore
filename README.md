# Network Core

一个能够用简洁的方式来构建通信服务的轻量级框架。

**I M P O R T A N T  此框架即将弃用**

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

在继承 **services.Idenfaction** 后，认证的方式请写在 **Idenfy** 方法中。之后覆盖 **app.idf** 。

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
    def command_name_1(conet:Conet):
    	pass
    
    def command_name_2(conet:Conet):
    	pass

app.extension(Serv)
```

在通过此方法拓展时，请勿在方法中添加 **self** ，同时方法的名称便是指令的名称。

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

