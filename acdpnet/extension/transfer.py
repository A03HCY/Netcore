from acdpnet.tools    import *
from acdpnet.services import *
from acdpnet.nodes    import *
import os
import shutil
import pathlib
import ast


class RemoteConnection(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class RemoteSystem(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class InfoSupport:
    description = {
        'alive':{
            'desc':'Test for checking connection',
            'args':[{}],
            'resp':'Type:Dict'
        },
        'activities':{
            'desc':'Get online nodes list',
            'args':[{}],
            'resp':'Type:List'
        }
    }

    def alive(conet:Conet):
        conet.sendata({'resp':'OK'})
    
    def activities(conet:Conet):
        conet.sendata(conet.idf.GetInfo())


class TransferSupport:
    description = {
        'trans':{
            'desc':'Send data from a node to another one',
            'args':[{
                'remote':'Type:String Desc:Target Mac'
            }],
            'resp':''
        },
        'multi_cmd':{
            'desc':'Send a command from a node to another one',
            'args':[{
                'remote':'Type:String Desc:Target Mac',
                'command':'Type:String Desc:Command to execute',
            }],
            'resp':'Unknow'
        },
        'flow_trans':{
            'desc':'TCP flow',
            'args':[{
                'remote':'Type:String Desc:Target Mac',
            }],
            'resp':'Unknow'
        },
    }

    def trans(conet:Conet):
        data = conet.get('data')
        remo = data.get('remote', '')
        remote = conet.idf.GetByMac(remo)
        if not remote:
            res = {
                'resp':'target is not online'
            }
            conet.sendata(res)
            return
        data['remote'] = conet.get('mac')
        res = {
            'command':'trans_data',
            'data':data
        }
        remote.sendata(res)
        conet.sendata({
            'resp':'OK'
        })
    
    def multi_cmd(conet:Conet):
        data = conet.get('data')
        remo = data.get('remote', '')
        rcmd = data.get('command', 'msg')
        remote = conet.idf.GetByMac(remo)
        if not remote:
            res = {
                'resp':'Inactive',
                'meta':data
            }
            conet.sendata(res)
            return
        data['remote'] = conet.get('mac')
        try:data.pop('command')
        except:pass
        res = {
            'command':rcmd,
            'data':data
        }
        remote.sendata(res)
        conet.sendata({
            'resp':'OK',
        })
    
    def flow_trans(conet:Conet):
        data = conet.get('data')
        remo = data.get('remote', '')
        remote = conet.idf.GetByMac(remo)
        if not remote:return
        safe = RanCode(4)
        conet.que.put(safe)
        remote.que.put(safe)
        conn = conet.conn
        header = b''
        while len(header) < 10:
            temp = conn.recv(1)
            header += temp
            if temp == b'':break

        length = ReadHead(header)[3]
        remote.conn.send(header)
        
        recvdata = 0
        buff     = 8192
        while recvdata < length:
            if length - recvdata > buff:
                temp = conn.recv(buff)
                recvdata += len(temp)
            else:
                temp = conn.recv(length - recvdata)
                recvdata += len(temp)
            if temp == b'':
                remote.conn.send(temp)
                break
            else:
                remote.conn.send(temp)

        conet.que.get()
        remote.que.get()
        conet.que.task_done()
        remote.que.task_done()


class FilesNodes:
    description = {
        'ls':{
            'desc':'Remote list a path info',
            'args':[{}],
            'resp':'Type:Dict'
        },
        'cd':{
            'desc':'Change work dir',
            'args':[{
                'path':'Type:String Target path'
            }],
            'resp':'Type:Dict'
        },
        'pwd':{
            'desc':'Get work dir',
            'args':[{}],
            'resp':'Type:Dict'
        },
        'rm':{
            'desc':'Remove a file',
            'args':[{
                'name':'Type:String Target file'
            }],
            'resp':'Type:Dict'
        },
        'rmdir':{
            'desc':'Remove a dir',
            'args':[{
                'path':'Type:String Target path'
            }],
            'resp':'Type:Dict'
        },
        'search':{
            'desc':'Search a file',
            'args':[{
                'key':'Type:String Target file keyword'
            }],
            'resp':'Type:Dict'
        },
        'get':{
            'desc':'Get remote file by flow_trans',
            'args':[{
                'name':'Type:String filename at pwd'
            }],
            'resp':'Type:Dict'
        },
        'fileraw':{
            'desc':'Read / Write raw data',
            'args':[{
                'path':'Type:String filename at pwd',
                'mode':'Type:String mode',
                'seek':'Type:Int',
                'buff':'Type:Int',
                'raw_':'write mode, raw data'
            }],
            'resp':'Type:Dict'
        },
    }

    def ls(conet:Conet):
        data = conet.get('data')
        path = data.get('path', './')
        raw  = data.get('raw', 'False')
        if raw == 'True':raw = True
        else:raw = False
        try:
            data['resp'] = List(path, raw).table
        except:
            data['resp'] = 'Error'
        resp = {
            'command':'multi_cmd',
            'data':data
        }
        conet.sendata(resp)
    
    def cd(conet:Conet):
        data = conet.get('data')
        path = data.get('path', './')
        try:
            os.chdir(path)
        except:pass
        data['resp'] = 'Done'
        resp = {
            'command':'multi_cmd',
            'data':data
        }
        conet.sendata(resp)
    
    def pwd(conet:Conet):
        data = conet.get('data')
        path = os.getcwd()
        data['resp'] = path
        resp = {
            'command':'multi_cmd',
            'data':data
        }
        conet.sendata(resp)
    
    def getsize(conet:Conet):
        data = conet.get('data')
        path = data.get('path', '')
        try:size = os.path.getsize(path)
        except:size = -1
        data['resp'] = size
        resp = {
            'command':'multi_cmd',
            'data':data
        }
        conet.sendata(resp)

    def rm(conet:Conet):
        data = conet.get('data')
        name = data.get('name', 'file.unknow')
        path = os.path.join(os.getcwd(), name)
        if not os.path.isfile(path):
            resp = 'Cannot be found'
        else:
            try:
                os.remove(path)
                resp = 'OK'
            except:
                resp = 'Failed'
        data['resp'] = resp
        resp = {
            'command':'multi_cmd',
            'data':data
        }
        conet.sendata(resp)
    
    def rmdir(conet:Conet):
        data = conet.get('data')
        path = data.get('path', '')
        if not os.path.isdir(path):
            resp = 'Cannot be found'
        else:
            try:
                shutil.rmtree(path)
                resp = 'OK'
            except:
                resp = 'Failed'
        data['resp'] = resp
        resp = {
            'command':'multi_cmd',
            'data':data
        }
        conet.sendata(resp)
    
    def search(conet:Conet):
        data = conet.get('data')
        key = data.get('key', '')

        p = pathlib.Path(os.getcwd())
        res = []
        ret = p.rglob(key)
        for item in ret:
            res.append(str(item))

        data['resp'] = res
        resp = {
            'command':'multi_cmd',
            'data':data
        }
        conet.sendata(resp)
    
    def mkfile(conet:Conet):
        data = conet.get('data')
        path = data.get('path', 'file.unknow')
        try:
            open(path, 'wb').close()
            status = 'OK'
        except:
            status = 'Failed'
        resp = {
            'command':'multi_cmd',
            'data':status
        }
        conet.sendata(resp)
    
    def fileraw(conet:Conet):
        data = conet.get('data')
        path = data.get('path', '')
        mode = data.get('mode', 'rb')
        code = data.get('code', 'utf-8')
        seek = data.get('seek', 0)
        buff = data.get('buff', 0)
        raw_ = data.get('raw_', '')
        if not os.path.isfile(path):
            data['resp'] = 'Connot be found'
            resp = {
                'command':'multi_cmd',
                'data':data
            }
            conet.sendata(resp)
            return
        
        if not 'b' in mode:
            with open(path, mode, encoding=code) as f:
                f.read(seek)
                if 'w' in mode:
                    f.write(raw_)
                    temp = 'OK'
                else:
                    temp = str(f.read(buff))
        else:
            with open(path, mode) as f:
                f.seek(seek)
                if 'w' in mode:
                    f.write(ast.literal_eval(raw_))
                    temp = 'OK'
                else:
                    temp = str(f.read(buff))
        
        data['resp'] = temp
        resp = {
            'command':'multi_cmd',
            'data':data
        }
        conet.sendata(resp)
    
    def push(conet:Conet):
        data = conet.get('data')
        path = data.get('path', './file.unknow')
        with open(path, 'wb') as f:
            target = RemoteGet(conet).To(f)
            target.Now()
    
    def get(conet:Conet):
        data = conet.get('data')
        name = data.get('name', 'file.unknow')
        path = data.get('path', 'file.unknow')
        if path == 'file.unknow':
            path = os.path.join(os.getcwd(), name)
        data['f_path'] = path
        if not os.path.isfile(path):
            data['resp'] = 'Connot be found'
            resp = {
                'command':'multi_cmd',
                'data':data
            }
            conet.sendata(resp)
            conet.recvdata(timeout=5)
            return
        
        data['resp'] = 'OK'
        resp = {
            'command':'multi_cmd',
            'data':data
        }
        conet.sendata(resp)
        conet.recvdata(timeout=5)

        with open(path, 'rb') as f:
            tar = RemotePush(data).From(f)
            tar.Now(conet)


class Local:
    def __init__(self, path):
        self.path = path


class RemoteFileObject:
    def __init__(self, rfs, path, mode, encoding='utf-8'):
        self.rfs  = rfs
        self.path = path
        self.mode = mode
        self.code = encoding
        self.size = 0
        self.now  = 0

        if not self.rfs.path.isfile(path):
            raise RemoteSystem('File cannot be found.')
        self.size = self.rfs.path.getsize(path)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def seek(self, ran):
        if ran <= self.size:
            self.now = ran

    def read(self, size=None):
        if not self.mode in ['r', 'rb']:
            return
        
        if size == None:
            size = self.size - self.now
        elif size + self.now > self.size:
            raise RemoteSystem('File Limited.')

        data = {
            'path':self.path,
            'seek':self.now,
            'code':self.code,
            'mode':self.mode,
            'buff':size,
        }
        self.rfs.send('fileraw', data=data)
        resp = self.rfs.node.recv(timeout=10)
        data = self.rfs.node.recv(timeout=10).get('data', {}).get('resp', 'ReadError')
        if data == 'Connot be found' or data == 'ReadError':
            return 'Error'
        if self.mode == 'rb':data = ast.literal_eval(data)
        self.now += size
        return data

    def write(self, data):
        if not self.mode in ['w', 'wb', 'w+', 'wb+']:
            return
        
        if 'b' in self.mode and type(data) != bytes:
            return
        elif type(data) != str:
            return

        data = {
            'path':self.path,
            'seek':self.now,
            'code':self.code,
            'mode':self.mode,
            'buff':size,
            'raw_':str(data)
        }
        self.rfs.send('fileraw', data=data)
        resp = self.rfs.node.recv(timeout=10)
        data = self.rfs.node.recv(timeout=10).get('data', {}).get('resp', 'ReadError')
        if data == 'Connot be found' or data == 'ReadError' or data!= 'OK':
            return 'Error'
        
        return data
    
    def close(self):
        pass

    def save(self, local, console=None):
        data = {
            'path':self.path
        }
        self.rfs.send('get', data=data)
        resp = self.rfs.node.recv(timeout=10)
        data = self.rfs.node.recv(timeout=10).get('data', {})
        print(data)
        if data.get('resp') != 'OK':
            return
        with open(local, 'wb') as f:
            target = RemoteGet(self.rfs.node.conet).To(f)
            if console:
                target.Now_Progress(console)
            else:
                target.Now()


class RemotePath:
    def __init__(self, rfs):
        self.rfs = rfs
    
    def exists(self, path):
        r_path, r_name = os.path.split(path)
        try:
            data = self.rfs.listdir(r_path)
        except:return False
        if r_name in data:return True
        else:return False

    def istype(self, path, tell):
        r_path, r_name = os.path.split(path)
        try:
            data = self.rfs.metadir(r_path)
        except:return False
        if r_name == '' and tell == 'D':return True
        res = []
        for i in data:
            if i[0] == r_name:
                res = i
                break
        if res == []:return False
        return i[-1] == tell

    def isfile(self, path):
        return self.istype(path, 'F')

    def isdir(self, path):
        if path == '.':return True
        return self.istype(path, 'D')
    
    def getsize(self, path):
        data = {
            'path':path
        }
        self.rfs.send('getsize', data=data)
        resp = self.rfs.node.recv(timeout=10)
        data = self.rfs.node.recv(timeout=10).get('data', {}).get('resp')
        return data
    
    def push(self, local, remote, console=None):
        r_path, r_name = os.path.split(remote)
        if not self.isdir(r_path):
            return 'NO'
        if not os.path.exists(local):
            return 'L NO'

        data = {
            'path':  remote,
            'remote':self.rfs.mac,
            'f_path':local
        }
        self.rfs.send('push', data=data)
        resp = self.rfs.node.recv(timeout=10)
        with open(local, 'rb') as f:
            target = RemotePush(data).From(f)
            if console:
                target.Now_Progress(self.rfs.node.conet, console)
            else:
                target.Now(self.rfs.node.conet)

        return 'OK'
        
    
    def copy(self, fm, to, console=None):
        if type(fm) == Local and type(to) == Local:
            return
        
        if type(fm) == Local:
            return self.push(fm.path, to, console=console)
        elif type(to) == Local:
            with self.rfs.open(fm, 'rb') as f:
                f.save(to.path, console=console)
        else:
            # mv
            pass


class RemoteFileSystem(RemoteExtension):
    def setup(self):
        self.path = RemotePath(self)
    
    def metadir(self, path):
        if path == '':path = './'
        data = {
            'path':path,
            'raw' :'True'
        }
        self.send('ls', data=data)
        resp = self.node.recv(timeout=10)
        data = self.node.recv(timeout=10).get('data', {}).get('resp', 'Error')
        if data == 'Error':
            raise RemoteSystem('Path is not exists')
        return data
    
    def listdir(self, path:str):
        data = self.metadir(path)
        ls = []
        for i in data:
            ls.append(i[0])
        return ls
    
    def mkfile(self, path):
        data = {
            'path':path
        }
        self.send('mkfile', data=data)
        resp = self.node.recv(timeout=10)
        data = self.node.recv(timeout=10).get('data', {}).get('resp', [])
        return data
    
    def remove(self, path:str='None'):
        data = {
            'path':path
        }
        self.send('rm', data=data)
        resp = self.node.recv(timeout=10)
        data = self.node.recv(timeout=10).get('data', {}).get('resp', [])
        return data
    
    def removedirs(self, name:str='None'):
        data = {
            'path':name
        }
        self.send('rmdir', data=data)
        resp = self.node.recv(timeout=10)
        data = self.node.recv(timeout=10).get('data', {}).get('resp', [])
        return data
    
    removedir = removedirs

    def open(self, path, mode, encoding='utf-8') -> RemoteFileObject:
        obj = RemoteFileObject(self, path, mode, encoding=encoding)
        return obj

