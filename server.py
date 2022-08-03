from acdpnet.services import Tree
from acdpnet.extension.transfer import TransferSupport

app = Tree()
app.idf.acessuid = {'A03HCY':'123456'}
app.token = 'ASDF'
app.extension(TransferSupport)

app.run('0.0.0.0', 1035)