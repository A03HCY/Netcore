from socketserver import ThreadingTCPServer, StreamRequestHandler
from acdpnet.tools import *
from acdpnet.extension.transfer import InfoSupport
import json


CONET_TOKEN = {}
COMMANDS    = {}
POLS        = {}

class Idenfaction:
    clearifiction = {
        'descr':['mac', 'os', 'version', 'name', 'meth', 'uid'],
    }

    def __init__(self):
        self.activite = []
        self.acessuid = {}
        self.setup()
    
    def setup(self):pass

    def Idenfy(self, account:str, key:str):
        if key == self.acessuid.get(account):
            return True
        else:
            return False

    def GetInfo(self):
        data = []
        for conet in self.activite:
            info = clearify(conet.Idata, self.clearifiction['descr'])
            data.append(info)
        return data

    def UniqueMacTest(self, mac:str):
        Unique = True
        for conet in self.activite:
            if conet.get('mac') == mac:Unique = False
        return Unique

    def RemoveMac(self, mac:str):
        for conet in self.activite:
            if conet.get('mac') == mac:
                self.activite.remove(conet)
                conet.close()
    
    def GetByMac(self, mac:str) -> Conet:
        for conet in self.activite:
            if conet.get('mac') == mac:return conet
    

class CoreTree(StreamRequestHandler):
    clearifiction = {
        'setup':['mac', 'version', 'uid', 'pwd', 'token'],
        'descr':['os', 'name', 'meth'],
        'handl':['command', 'data']
    }
    timeout  = 300

    def idenfy(self, data):
        global CONET_TOKEN
        if data['token'] != CONET_TOKEN[self.cmdid]:return False
        print('Token OK')
        if not POLS[self.cmdid].Idenfy(data['uid'], data['pwd']):return False
        return True

    def setup(self):
        print('New')
        self.request.settimeout(self.timeout)
        self.conet  = Conet(self.request, mode='TCP')
        self.cmdid  = self.server.server_address[1]
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
        try:
            res = {
                'meth':list(COMMANDS[self.cmdid].keys())
            }
            self.conet.sendata(res)
        except:
            return
        self.conet.Idata.update(req)
        self.conet.Idata.update(descr)
        self.status = True
        POLS[self.cmdid].RemoveMac(self.conet.get('mac'))
        POLS[self.cmdid].activite.append(self.conet)
        
    def handle(self):
        global COMMANDS
        if not self.status:return
        while True:
            try:
                data, passable = clearify(self.conet.recvdata(), self.clearifiction['handl'])
                self.conet.save('args', (data, passable))
                self.conet.save('data', data.get('data'))
            except socket.timeout:
                break
            except:
                break

            if data['command'] in COMMANDS[self.cmdid].keys():
                self.conet.idf = POLS[self.cmdid]
                COMMANDS[self.cmdid][data['command']](self.conet)
            else:
                pass


    def finish(self):
        print('Out of', self.conet.get('mac'))
        POLS[self.cmdid].RemoveMac(self.conet.get('mac'))


class Tree:
    def __init__(self, idf=Idenfaction()):
        self.meth = {}
        self.mdes = {}
        self.idf  = idf
        self.extension(InfoSupport)

    def command(self, cmd=None):
        def decorator(func):
            self.meth[cmd] = func
            return func
        return decorator
    
    def extension(self, ext):
        for name in dir(ext):
            if name == 'description':continue
            if name.startswith('_'):continue
            self.meth[name] = getattr(ext, name)
            self.mdes[name] = getattr(ext, 'description').get(name, [])
    
    def run(self, ip:str, port:int, token:str=None):
        if token:self.token = token
        CONET_TOKEN[port] = self.token
        COMMANDS[port]    = self.meth
        POLS[port]        = self.idf
        addr = (ip, port)
        server = ThreadingTCPServer(addr, CoreTree)
        server.serve_forever()