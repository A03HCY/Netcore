from acdpnet.services import *
from acdpnet.extension.transfer import *

class AT(Idenfaction):
    def setup(self):
        pass

    def Idenfy(self, account:str, key:str):
        if key == self.acessuid.get(account):
            return True
        else:
            return False

app = Tree()

app.extension(TransferSupport)

app.idf.acessuid
app.token = "ASDF"

app.run('0.0.0.0', 1035)