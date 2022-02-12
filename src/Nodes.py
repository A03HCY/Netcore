from Tools import *
import json
import uuid


def GetMac():
    mac = uuid.UUID(int = uuid.getnode()).hex[-12:]
    return ":".join([mac[e:e+2] for e in range(0, 11, 2)])


class BasicNode:
    def __init__(self, description:str):
        self.conet = Conet(mode='TCP')
        self.description = description

    def connect(self, address:tuple, conet_pwd:str):
        self.conet.save('address', address)
        self.conet.connect(address)

        msg = {
            "conet_pwd":conet_pwd,
            "mac_addr":GetMac(),
            'description':self.description
        }
        self.server(Before(msg))

        recv_data = self.recv()
        res = After(recv_data[0].meta)
        print('res', res)
        if not res['status']:
            raise ConnectionRefusedError('Password Error')
        self.uid = recv_data[1]
        self.sever_version = res['version']
    
    def close(self):
        self.conet.close()
    
    def send(self, uid, data, head=[255,255]):
        if type(uid) != bytes:uid = bytes(uid)
        data = BasicProtocol(data)
        data.exps_data = list(uid)
        data.type_code = head[0]
        data.cont_code = head[1]
        self.conet.force_send(data.GetFull())
    
    def server(self, data, head=[255,255]):
        self.send([255,255,255,255], data, head=head)
    
    def force_send(self, data):
        self.conet.force_send(data)
    
    def recv(self):
        data = self.conet.recv(protocal=True)
        return data, bytes(data.exps_data)
    
    def handle(self): ...

    def finish(self):
        msg = {
            "command":"exit"
        }
        self.server(Before(msg))
        self.conet.close()


# As a sensor node
class Sensor(BasicNode):
    def __init__(self):
        pass

# As a database node
class Database(BasicNode):
    def __init__(self):
        pass

# As a storage node
class Storage(BasicNode):
    def __init__(self):
        pass

# As a proxy node
class Proxy(BasicNode):
    def __init__(self):
        pass

# As an operable node
class Operation(BasicNode):
    def __init__(self):
        pass


def StartAsService(nodefunc, address, pwd, description):
    node = nodefunc(description)
    node.connect(address, pwd)
    node.handle()
    node.finish()