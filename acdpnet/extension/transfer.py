from acdpnet.tools    import *
from acdpnet.services import *
import os

class InfoSupport:
    description = {
        'alive':[],
        'activities':[]
    }

    def alive(conet:Conet):
        conet.sendata({'resp':'OK'})
    
    def activities(conet:Conet):
        conet.sendata(conet.idf.GetInfo())


class TransferSupport:
    description = {
        'alive':[],
        'activities':[]
    }

    def trans(conet:Conet):
        data = conet.get('data')
        remo = data.get('remote', '')
        remote = conet.idf.GetByMac(remo)
        if not remote:
            res = {
                'respond':'Inactive',
                'meta':data
            }
            conet.sendata(res)
            return
        data['remote'] = conet.get('mac')
        res = {
            'command':'trans_data',
            'data':data
        }
        remote.sendata(res)
    
    def multi_cmd(conet:Conet):
        data = conet.get('data')
        remo = data.get('remote', '')
        rcmd = data.get('command', 'msg')
        remote = conet.idf.GetByMac(remo)
        if not remote:
            res = {
                'respond':'Inactive',
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


class FilesNodes:
    description = {
        'alive':[],
        'activities':[]
    }

    def ls(conet:Conet):
        data = conet.get('data')
        path = data.get('path', './')
        data['resp'] = os.listdir(path)
        resp = {
            'command':'multi_cmd',
            'data':data
        }
        conet.sendata(resp)