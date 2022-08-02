from socketserver import ThreadingTCPServer, StreamRequestHandler
from Tools import *
import json


CONET_TOKEN = 'R3i0gdh2G3QHR094'

COMMANDS = {}
POLS = {}

class Idenfaction:
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

    def GetInfo(self, account:str):
        pass

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
    

class CoreTree(StreamRequestHandler):
    clearifiction = {
        'setup':['mac', 'version', 'uid', 'pwd', 'token'],
        'descr':['os', 'name'],
        'handl':['command', 'data']
    }
    timeout  = 300

    def idenfy(self, data):
        global CONET_TOKEN
        if data['token'] != CONET_TOKEN:return False
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
            except socket.timeout:
                break
            except:
                break

            if data['command'] in COMMANDS[self.cmdid].keys():
                COMMANDS[self.cmdid][data['command']](self.conet)
            else:
                pass


    def finish(self):
        print('Out of', self.conet.get('mac'))
        POLS[self.cmdid].RemoveMac(self.conet.get('mac'))


class Tree:
    def __init__(self, idf=Idenfaction()):
        self.meth = {}
        self.idf  = idf

    def command(self, cmd=None):
        def decorator(func):
            self.meth[cmd] = func
            return func
        return decorator
    
    def run(self, ip:str, port:int):
        COMMANDS[port] = self.meth
        POLS[port] = self.idf
        addr = (ip, port)
        server = ThreadingTCPServer(addr, CoreTree)
        server.serve_forever()