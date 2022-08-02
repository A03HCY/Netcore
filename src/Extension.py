from Tools    import *
from Services import *

class Transfer:
    def bye(conet:Conet):
        data = conet.get('data')
        conet.idf.GetByMac(conet.get('mac')).close()

    
a = Tree()

a.extension(Transfer)
a.idf.acessuid = {'cons':'123456'}

print(a.meth)

a.run('0.0.0.0', 1035, 'hi')