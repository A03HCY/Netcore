'''
Copyright (c) 2021 https://gitee.com/intellen
Intellen - Network is licensed under Mulan PSL v2.
You can use this software according to the terms and conditions of the Mulan PSL v2. 
You may obtain a copy of Mulan PSL v2 at:
            http://license.coscl.org.cn/MulanPSL2 
THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.  
See the Mulan PSL v2 for more details. 

Url     : https://gitee.com/intellen/network
'''
from socketserver import ThreadingTCPServer, StreamRequestHandler
from Ucode import *

CONN_WORD = '123456'
CONN_PORT = 1305


class Boxcon:
    '''Manage nodes'''
    def __init__(self):
        self.list = []
    
    def add(self, con:Consiver):
        self.list.append(con)
    
    def listall(self):
        data = []
        for con in self.list:
            data.append(con.Idata)
        return data
    
    def search(self, uid):
        for con in self.list:
            temp_uid = con.get('uid')
            if temp_uid == uid:return con
    
    def remove(self, uid):
        con = self.search(uid)
        if con == None:return False
        self.list.remove(con)
        return True

conbox = Boxcon()

class CoreTree(StreamRequestHandler):
    def setup(self):
        '''Confirm Connection'''
        # Init
        self.confirm = False
        self.uid = ''
        self.cons = Consiver(self.request, 'TCP')

        # Recv Info
        try:
            data = self.cons.recv().decode('utf-8')
            data = ast.literal_eval(data)
            if type(data) != dict:return
        except:return

        # Confirm and Save
        if data.get('_PWD') != CONN_WORD:return
        for key, values in data.items():
            if key[0] == '_':continue
            self.cons.save(key, values)
        if not self.cons.get('uid'):self.cons.save('uid', RanID())

        # Pass Confirm by sending uid
        self.uid = self.cons.get('uid')
        try:self.cons.send(self.uid.encode('utf-8'))
        except:return
        conbox.add(self.cons)
        self.confirm = True
        print('I:', self.uid)
    
    def trans(self, data):
        target = data.get('target')
        print('T:', target)
        size = int(data.get('size'))
        buff = int(data.get('buff', '1024'))

        # ------ Waiting to be fixed

        con = conbox.search(target)
        if not con:
            self.cons.send('Not'.encode('utf-8'))
            return

        # -------
        con.send(str([data.get('name','temp.cot'), size, buff]).encode('utf-8'))
        self.cons.send('Con'.encode('utf-8'))
        while size > 0:
            if size - 2048 > 0:
                temp = self.cons.conn.recv(2048)
            else:
                temp = self.cons.conn.recv(size)
            con.conn.send(temp)
            size -= len(temp)
        con.close()
    
    def execute(self, data):
        # Get command
        reda = ''
        cmd = data.pop('cmd')

        # Do something
        if cmd == 'lsc':
            reda = conbox.listall()
        if cmd == 'trans':
            self.trans(data)
            return
        
        # Return result
        ret = {
            'sender':'_server',
            'time':time.time(),
            '_add':data.get('_add', ''),
            '_data':reda
        }
        try:self.cons.send(str(ret).encode('utf-8'))
        except:self.cons.close()
    
    def forward(self, data):
        con = conbox.search(data.pop('recver'))
        if not con:return
        met = data.pop('method', 'clt')
        data['time'] = time.time()
        if met == 'clt':
            data['sender'] = self.uid
        elif met == 'sev':
            data['sender'] = '_server'
        else:
            data['sender'] = self.uid
        try:con.send(str(data).encode('utf-8'))
        except:con.close()
    
    def handle(self):
        if not self.confirm:return
        while True:
            try:
                data = self.cons.recv().decode('utf-8')
                data = ast.literal_eval(data)
            except:return
            dtype = data.pop('_type')

            # execute
            if dtype == 'cmd':
                self.execute(data)
            # Trans data
            if dtype == 'for':
                self.forward(data)

    def finish(self):
        conbox.remove(self.uid)
        print('O:', self.uid)


def start():
    print('Start on port', CONN_PORT)
    addr = ('0.0.0.0',CONN_PORT)
    server = ThreadingTCPServer(addr, CoreTree)
    server.serve_forever()


if __name__ == "__main__":
    start()