from socketserver import ThreadingTCPServer, StreamRequestHandler
from Tools import *
import json


CONET_TOKEN = 'R3i0gdh2G3QHR094'


class Idenfaction:
    def __init__(self):
        self.activite = []
        self.acessuid = {'cons':'12345678'}

    def Idenfy(self, account:str, key:str):
        if key == self.acessuid.get(account):
            return True
        else:
            return False

    def GetInfo(self, account:str):
        pass
    
pols = Idenfaction()

class CoreTree(StreamRequestHandler):
    clearifiction = {
        'setup':['mac', 'version', 'uid', 'pwd', 'token'],
        'descr':['mac', 'version', 'uid', 'os', 'name'],
        'handl':['command', 'data']
    }
    def __init__(self):
        self.timeout  = 300
        self.commands = {}

    def command(self, cmd=None):
        def decorator(func):
            self.commands[cmd] = func
            return func
        return decorator

    def idenfy(self, data):
        global CONET_TOKEN, pols
        if data['token'] != CONET_TOKEN:return False
        if not pols.idenfy(data['uid'], data['pwd']):return False
        return True

    def setup(self):
        self.request.settimeout(self.timeout)
        self.conet  = Conet(self.request, mode='TCP')
        self.status = False

        try:
            req, passable = clearify(self.conet.recvdata(), self.clearifiction['setup'])
            if (not passable) or (not self.idenfy(req)):return
        except:return
        descr, passable = clearify(self.conet.recvdata().update(req), self.clearifiction['descr'])
        if not passable:return
        self.conet.Idata.update(descr)
        self.status = True
        pols.activite.append(self.conet)
        
    def handle(self):
        if not self.status:return
        while True:
            try:
                data, passable = clearify(self.conet.recvdata(), self.clearifiction['handl'])
            except socket.timeout:
                break
            except:
                break
            if data[0] in self.commands:
                self.commands[data[0]](self.conet)
            else:
                pass


    def finish(self):
        if self.conet in pols.activite:
            pols.activite.remove(self.conet)


def Start(service, port):
    addr = ('0.0.0.0',port)
    server = ThreadingTCPServer(addr, service)
    server.serve_forever()




if __name__ == "__main__":
    app = CoreTree()

    @app.command('wer')
    def a(conet:Conet):
        pass

    Start(app, 3377)