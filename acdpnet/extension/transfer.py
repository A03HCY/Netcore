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
                'remote':'Type:String Desc:Target\'s Mac'
            }],
            'resp':''
        },
        'multi_cmd':{
            'desc':'Send a command from a node to another one',
            'args':[{
                'remote':'Type:String Desc:Target\'s Mac',
                'command':'Type:String Desc:Command to execute',
            }],
            'resp':'Unknow'
        }
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