from socketserver import ThreadingTCPServer, StreamRequestHandler
from Tools import *
import json


CONET_PWD = 'R3i0gdh2G3QHR094'


class ConetPool:
    def __init__(self):
        self.pool = {}
    
    def free(self):
        keys = self.pool.keys()
        frid = [0, 0, 0, 0]
        for nosk in range(0, 4):
            for i in range(0, 256):
                if (nosk == 3) and (i == 255):raise MemoryError('ID Fulled')
                frid[nosk] = i
                if not bytes(frid[::-1]) in keys:
                    return bytes(frid[::-1])
        raise MemoryError('IP Fulled')

    def new(self, conet):
        uid = self.free()
        self.pool[uid] = conet
        return uid

    def remove(self, uid):
        if type(uid) != bytes:uid = bytes(uid)
        self.pool.pop(uid)

    def listall(self):
        return self.pool.keys()

    def conet(self, uid):
        if type(uid) != bytes:uid = bytes(uid)
        return self.pool.get(uid)
    

pols = ConetPool()

class CoreTree(StreamRequestHandler):
    def setup(self):
        global CONET_PWD, pols
        conet = Conet(self.request, mode='TCP')

        req = After(conet.recv())
        print('req', req)
        self.status = False
        self.exit = False
        if req.get('conet_pwd') == CONET_PWD:
            self.status = True
        resp = {
            "status":self.status,
            "version":VERS
        }

        if not self.status:
            print('No')
            resp = BasicProtocol(Before(resp), exps_data=[255,255,255,255]).GetFull()
            conet.force_send(resp)
            conet.close()
            return
        
        self.conet = conet
        self.mac = req.get('mac_addr')
        self.conet.save('mac', self.mac)
        self.description = req.get('description')
        self.conet.save('mac', self.description)
        self.uid = pols.new(self.conet)

        resp = BasicProtocol(Before(resp), exps_data=list(self.uid)).GetFull()
        self.conet.force_send(resp)

        print(self.mac, 'logint as node id', IPShow(self.uid))

    def transer(self, proto):
        pass
    
    def execute(self, head, data):
        cmd = data.get('command')

        if cmd == 'exit':
            self.exit = False
    
    def handle(self):
        if not self.status:return
        global pols
        SEVID = bytes([255,255,255,255])
        while True:
            try:
                if not self.exit:return
                recv = self.conet.recv(protocal=True)
                head = [recv.type_code, recv.cont_code]
                tuid = bytes(recv.exps_data)
                data = After(recv.meta)
            except:return

            if (tuid == SEVID) or (tuid == self.uid):
                self.execute(head, data)
                continue
            else:
                self.transer(recv)


    def finish(self):
        if not self.status:return
        global pols
        print(self.mac, 'logout as node id', IPShow(self.uid))
        pols.remove(self.uid)
        self.conet.close()



def Start(service, port):
    addr = ('0.0.0.0',port)
    server = ThreadingTCPServer(addr, service)
    server.serve_forever()


if __name__ == "__main__":
    Start(CoreTree, 3377)