from acdpnet.tools import *
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
        'descr':['os', 'name', 'meth'],
        'handl':['command', 'data']
    }
    status = False
    remote = ''
    
    def __init__(self, uid:str, pwd:str):
        self.conet = Conet()
        self.conet.Idata.update({
            'uid':uid,
            'pwd':pwd,
            'mac':GetMac(),
            'version':VERS,
            'os':platform.platform(),
            'name':platform.node(),
            'meth':[]
        })
        self.meth   = {}
        self.mdes   = {}
        self.server = {}
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
        except:
            print('Error')
        self.idenfy()
        self.remote = 'server'
    
    def idenfy(self):
        self.conet.Idata.update({
            'meth':self.mdes,
        })
        self.conet.sendata(clearify(self.conet.Idata, self.clearifiction['setup'])[0])
        self.conet.sendata(clearify(self.conet.Idata, self.clearifiction['descr'])[0])
        self.server = self.conet.recvdata()
    
    def close(self):
        self.conet.close()
    
    def recv(self, timeout=0) -> dict:
        data = self.conet.recvdata(timeout=timeout)
        return data
    
    def send(self, command:str, data:dict={}):
        resp = {
            'command':command,
            'data':data
        }
        self.conet.sendata(resp)


class ExtensionSupportNode(BasicNode):
    def extension(self, ext):
        for name in dir(ext):
            if name == 'description':continue
            if name.startswith('_'):continue
            self.meth[name] = getattr(ext, name)
            if 'description' in dir(ext):
                self.mdes[name] = getattr(ext, 'description').get(name, {})
            else:
                self.mdes[name] = {}
    
    def command(self, cmd:str='None'):
        def decorator(func):
            self.meth[cmd] = func
            self.mdes[cmd] = {}
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