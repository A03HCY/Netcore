from acdpnet.tools    import *
from acdpnet.services import *
import os
import shutil
import pathlib


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
    }

    def ls(conet:Conet):
        data = conet.get('data')
        path = data.get('path', './')
        data['resp'] = List(path).table
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
    
    def get(conet:Conet):
        data = conet.get('data')
        name = data.get('name', 'file.unknow')
        path = os.path.join(os.getcwd(), name)
        if not os.path.isfile(path):
            data['resp'] = 'Connot be found'
            resp = {
                'command':'multi_cmd',
                'data':data
            }
            conet.sendata(resp)
            return
        
        data['resp'] = 'OK'
        resp = {
            'command':'multi_cmd',
            'data':data
        }
        conet.sendata(resp)
        
        size   = os.path.getsize(path)
        prot   = BasicProtocol()
        header = prot.GetHead(length=size)

        with open(path, 'rb') as f:
            resp = {
                'command':'flow_trans',
                'data':data
            }
            conet.sendata(resp)
            conet.que.put(RanCode(4))
            conn = conet.conn
            conn.send(header)
            
            length = size
            sended = 0
            buff   = 8192
            while sended < length:
                if length - sended > buff:
                    temp = f.read(buff)
                    sended += len(temp)
                else:
                    temp = f.read(length - sended)
                    sended += len(temp)
                conn.send(temp)
            
            conet.que.get()
            conet.que.task_done()