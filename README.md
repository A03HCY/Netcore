# Netcore

![](https://badgen.net/github/license/A03HCY/Netcore) ![](https://badgen.net/github/release/A03HCY/Netcore/stable)


一个用于简化数据传输流程的库。它能解决流传输粘包、使单个连接并行传输，且支持原格式传输，简化相关开发代码。

## 安装

Netcore 已上传至 PYPI 与 Github，使用以下其一命令即可快速安装。

通过 pip 安装。

```bash
pip install netcore
# OR
pip install git+https://github.com/A03HCY/Netcore.git
```

通过 git clone 进行源码安装。

```bash
git clone https://github.com/A03HCY/Netcore.git
cd Netcore
python setup.py install
```

## 简单使用

Netcore 可使用类 Flask 框架拓展业务，无需写繁琐的条件判断，对项目有良好的可维护性。

```python
from netcore.endpoint import Endpoint, get_request

app = Endpoint(...)

@app.route('.path')
def func():
    req = get_request()
    data = req.data
    return '.another_path', 'msg'

app.start(thread=True)

# do sth.
```

同时，也可以继承 Endpoint 实现相关业务。

```python
from netcore.endpoint import Endpoint, get_request

class Example(Endpoint):
    def on_path(self): # on_ + 'your_path'
        req = get_request()
        data = req.data
        return '.another_path', 'msg'

app = Example(...)
app.start(thread=True)

# do sth.
```