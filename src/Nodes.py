from Tools import *
import platform
import json
import uuid
import time


def GetMac():
    mac = uuid.UUID(int = uuid.getnode()).hex[-12:]
    return ":".join([mac[e:e+2] for e in range(0, 11, 2)])


class BasicNode:
    clearifiction = {
        'setup':['mac', 'version', 'uid', 'pwd', 'token'],
        'descr':['os', 'name'],
        'handl':['command', 'data']
    }
    status = False
    
    def __init__(self, uid:str, pwd:str):
        self.conet = Conet()
        self.conet.Idata.update({
            'uid':uid,
            'pwd':pwd,
            'mac':GetMac(),
            'version':VERS,
            'os':platform.platform(),
            'name':platform.node()
        })
        self.setup()
    
    def setup(self):
        pass

    def connect(self, address:tuple, token:str):
        self.conet.Idata.update({
            'adr':str(address),
            'token':token
        })
        try:
            self.conet.connect(address)
            self.idenfy()
        except:
            print('Error')
    
    def idenfy(self):
        self.conet.sendata(clearify(self.conet.Idata, self.clearifiction['setup'])[0])
        self.conet.sendata(clearify(self.conet.Idata, self.clearifiction['descr'])[0])
    
    def close(self):
        self.conet.close()
    
    def cmd(self, s, d={}):
        data = {
            'command':s,
            'data':d
        }
        self.conet.sendata(data)


class ServiceNode(BasicNode):
    def setup(self):
        self.meth = {}
    
    def extension(self, ext):
        for name in dir(ext):
            if name.startswith('_'):continue
            self.meth[name] = getattr(ext, name)
    
    def command(self, cmd=None):
        def decorator(func):
            self.meth[cmd] = func
            return func
        return decorator

    def run(self):
        while True:
            try:
                data, passable = clearify(self.conet.recvdata(), self.clearifiction['handl'])
                self.conet.save('args', (data, passable))
                self.conet.save('data', data.get('data'))
            except socket.timeout:
                break
            except:
                break

            if data['command'] in self.meth.keys():
                self.meth[data['command']](self.conet)
            else:
                pass


class T:
    def hi(conet:Conet):
        data = conet.get('data')
        print(data)
        data['command'] = 'multi_cmd_res'
        res = {
            'command':'multi_cmd',
            'data':data
        }
        conet.sendata(res)


app = ServiceNode('cons', '123456')

app.extension(T)

app.connect(('localhost', 1035), 'hi')

time.sleep(1)

app.close()

app.run()
