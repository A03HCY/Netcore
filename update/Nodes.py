from Tools import *
import json
import uuid


def GetMac():
    mac = uuid.UUID(int = uuid.getnode()).hex[-12:]
    return ":".join([mac[e:e+2] for e in range(0, 11, 2)])


class BasicNode:
    def __init__(self, description:str):
        pass

    def connect(self, address:tuple, conet_pwd:str):
        pass
    
    def close(self):
        self.conet.close()
    
    def send(self, uid, data, head=[255,255]):
        pass
    
    def recv(self):
        data = self.conet.recv(protocal=True)
        return data, bytes(data.exps_data)
    
    def handle(self): ...

    def finish(self):...