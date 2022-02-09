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
from Ucode import *


class Transer(threading.Thread):
    def __init__(self, addr:tuple, pwd:str, path:str, mode='recv', tar='', buff=2048):
        threading.Thread.__init__(self)
        self.uid = RanID()
        self.tar = tar
        self.mode = mode
        self.path = path
        self.buff = buff
        self.cons = CreatTree(addr, pwd, self.uid)
    
    def recv(self):
        data = self.cons.recv().decode('utf-8')
        data = ast.literal_eval(data)
        name = data[0]
        size = a = int(data[1])
        buff = a = int(data[2])
        with open(os.path.join(self.path, name), 'wb') as f:
            while size > 0:
                if size - buff > 0:
                    temp = self.cons.conn.recv(buff)
                else:
                    temp = self.cons.conn.recv(size)
                f.write(temp)
                size -= len(temp)
        self.cons.close()

    def send(self):
        size = os.path.getsize(self.path)
        data = {
            'cmd':'trans',
            'target':self.tar,
            'size':size,
            'buff':self.buff,
            'name':os.path.split(self.path)[1],
            '_type':'cmd'
        }
        self.cons.send(str(data).encode('utf-8'))
        res = self.cons.recv().decode('utf-8')
        if res == 'Not':return
        print('S',self.buff)
        with open(self.path, 'rb') as f:
            while size > 0:
                if size - self.buff > 0:
                    temp = f.read(self.buff)
                else:
                    temp = f.read(size)
                self.cons.conn.send(temp)
                size -= len(temp)
        self.cons.close()

    def run(self):
        if self.mode == 'recv':self.recv()
        if self.mode == 'send':self.send()


class Reconer(threading.Thread):
    def __init__(self, cons:Consiver, recv_que:queue.Queue, serv_que:queue.Queue):
        threading.Thread.__init__(self)
        self.cons = cons
        self.comd_que = queue.Queue()
        self.recv_que = recv_que
        self.serv_que = serv_que
    
    def Uncraft(self, data):
        data = ast.literal_eval(data)
        ordata = data.pop('_data')
        return ordata, data
    
    def __send(self, method, data):
        data['_type'] = method
        self.cons.send(str(data).encode('utf-8'))
    
    def handle(self, data):
        # Get command
        recver = data[1].get('sender')
        args = data[1]['_args']
        add = data[1].get('_add')
        cmd = data[0]
        reda = ''

        # Do something
        if cmd == 'system':
            reda = list(platform.uname())
        if cmd == 'list':
            path = args.get('path', './')
            tree = args.get('tree', False)
            reda = Indexall(path, tree)
        
        if cmd == 'get':
            target = data[1].get('uid')
            buff = int(args.get('buff', '2048'))
            path = args.get('path')
            Transer(self.cons.get('addr'), self.cons.get('_PWD'), path, mode='send', tar=target, buff=buff).start()
            return

        # Return result
        rdata = {
            'method':'sev',
            'recver':recver,
            '_data':reda,
            '_add':add
        }
        self.__send('for', rdata)
    
    def run(self):
        while True:
            # Get and Handle
            try:data = self.cons.recv().decode('utf-8')
            except:break
            data = self.Uncraft(data)

            # Put into que
            if data[1].get('sender') == '_server':
                self.serv_que.put(data)
            elif data[1].get('_handle') == True:
                self.handle(data)
            else:self.recv_que.put(data)


class Toconer:
    def __init__(self, address:tuple, password:str):
        self.Alive = False
        self.addr = address
        self.pwd = password
        self.uid = RanID()
        self.recv_que = queue.Queue()
        self.serv_que = queue.Queue()
        self.reset()
    
    def __send(self, method, data):
        data['_type'] = method
        self.cons.send(str(data).encode('utf-8'))
    
    def __serv(self, safecode, miss=True):
        start_time = real_time = time.time()
        while True:
            uesd_time = time.time() - start_time
            real_uesd = time.time() - real_time
            res = self.serv_que.get()
            if res[1].get('_add') == safecode:
                self.serv_que.task_done()
                return res
            if miss == False:continue
            if uesd_time > SAFE_TIME:
                start_time = time.time()
                self.serv_que.task_done()
            if real_uesd > OUT_TIME:
                return ('', {'sender':'_local', 'time':start_time})
    
    def listnodes(self) -> list:
        safecode = RanCode(4)
        data = {
            'cmd':'lsc',
            '_add':safecode
        }
        self.__send('cmd', data)
        res = self.__serv(safecode)
        return res[0]
    
    def send(self, tdata, uid):
        data = {
            'method':'clt',
            'recver':uid,
            '_data':tdata,
        }
        self.__send('for', data)
    
    def recv(self):
        data = self.recv_que.get()
        self.recv_que.task_done()
        return data
    
    def reset(self):
        self.close()
        self.cons = CreatTree(self.addr, self.pwd, self.uid)
        self.Alive = True
        self.rec = Reconer(self.cons, self.recv_que, self.serv_que)
        self.rec.start()
    
    def join(self):
        self.rec.join()

    def close(self):
        try:
            self.Alive = False
            self.cons.close()
        except:pass
    
    def Remote(self, cmd:str, uid:str, **args):
        safecode = RanCode(4)
        miss = True
        data = {
            'method':'clt',
            'recver':uid,
            '_add':safecode,
            '_data':cmd,
            '_handle':True,
            '_args':args
        }

        if cmd == 'get':
            temp = Transer(self.addr, self.pwd, args.get('local', './'), mode='recv')
            data['uid'] = temp.uid
            temp.start()

        self.__send('for', data)

        if cmd == 'get':return
        if cmd == 'list':miss = False

        res = self.__serv(safecode, miss=miss)

        if cmd == 'list':res = Initall(res[0])
        if cmd == 'system':res = res[0]

        return res
        pass