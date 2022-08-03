from acdpnet.tools    import *
from acdpnet.services import *

class TransferSupport:
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
        rcmd = data.get('command', '')
        remote = conet.idf.GetByMac(remo)
        if not remote:
            res = {
                'respond':'Inactive',
                'meta':data
            }
            conet.sendata(res)
            return
        data['remote'] = conet.get('mac')
        data.pop('command')
        res = {
            'command':rcmd,
            'data':data
        }
        remote.sendata(res)