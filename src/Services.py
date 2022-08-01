from socketserver import ThreadingTCPServer, StreamRequestHandler
from Tools import *
import json


CONET_TOKEN = 'R3i0gdh2G3QHR094'

COMMANDS = {}

def command(cmd=None):
    def decorator(func):
        COMMANDS[cmd] = func
        return func
    return decorator

class Idenfaction:
    def __init__(self):
        self.activite = []
        self.acessuid = {'cons':'12345678'}

    def Idenfy(self, account:str, key:str):
        print(account, key)
        if key == self.acessuid.get(account):
            return True
        else:
            return False

    def GetInfo(self, account:str):
        pass
    
POLS = Idenfaction()

class CoreTree(StreamRequestHandler):
    clearifiction = {
        'setup':['mac', 'version', 'uid', 'pwd', 'token'],
        'descr':['mac', 'version', 'uid', 'os', 'name'],
        'handl':['command', 'data']
    }
    timeout  = 300

    def idenfy(self, data):
        global CONET_TOKEN, POLS
        if data['token'] != CONET_TOKEN:return False
        if not POLS.Idenfy(data['uid'], data['pwd']):return False
        return True

    def setup(self):
        print('New')
        self.request.settimeout(self.timeout)
        self.conet  = Conet(self.request, mode='TCP')
        self.status = False

        try:
            req, passable = clearify(self.conet.recvdata(), self.clearifiction['setup'])
            if (not passable) or (not self.idenfy(req)):return
        except socket.timeout:
            return
        except:
            return
        try:
            data = self.conet.recvdata()
            data.update(req)
            descr, passable = clearify(data, self.clearifiction['descr'])
        except:
            return
        if not passable:return
        self.conet.Idata.update(descr)
        self.status = True
        POLS.activite.append(self.conet)
        
    def handle(self):
        if not self.status:return
        while True:
            try:
                data, passable = clearify(self.conet.recvdata(), self.clearifiction['handl'])
                self.conet.save('args', (data, passable))
            except socket.timeout:
                break
            except:
                break

            if data[0] in COMMANDS:
                COMMANDS[data[0]](self.conet)
            else:
                pass


    def finish(self):
        print('Out')
        if self.conet in POLS.activite:
            POLS.activite.remove(self.conet)
        self.conet.close()


def Start(service, port):
    addr = ('0.0.0.0',port)
    server = ThreadingTCPServer(addr, service)
    server.serve_forever()




if __name__ == "__main__":
    @command('as')
    def aa(conet):
        print('as cmd')

    Start(CoreTree, 3377)
