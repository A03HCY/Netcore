from Tools    import *
from Services import *

class ServiceNodeSupport:
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


class Transfer:
    def trans(conet:Conet):
        pass

    
a = Tree()

a.extension(ServiceNodeSupport)
a.idf.acessuid = {'cons':'123456'}

print(a.meth)

a.run('0.0.0.0', 1035, 'hi')