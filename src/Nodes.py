from Tools import *
import json
import uuid
import time


def GetMac():
    mac = uuid.UUID(int = uuid.getnode()).hex[-12:]
    return ":".join([mac[e:e+2] for e in range(0, 11, 2)])


class BasicNode:
    clearifiction = {
        'setup':['mac', 'version', 'uid', 'pwd', 'token'],
        'descr':['mac', 'version', 'uid', 'os', 'name'],
        'handl':['command', 'data']
    }
    status = False
    
    def __init__(self, uid:str, pwd:str):
        self.conet = Conet()
        self.conet.Idata.update({
            'uid':uid,
            'pwd':pwd,
            'mac':GetMac(),
            'version':'0.0.0',
            'os':'A',
            'name':'A'
        })

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
        #self.conet.sendata(self.conet.Idata)
        #self.conet.sendata(self.conet.Idata)
        print(self.conet.Idata)
    
    def close(self):
        self.conet.close()


ts = int(input('# '))
app = BasicNode('cons', '12345678')
app.connect(('localhost', 3377), 'R3i0gdh2G3QHR094')
time.sleep(ts)