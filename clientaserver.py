from acdpnet.nodes import ExtensionSupportNode
from acdpnet.extension.transfer import FilesNodes

app = ExtensionSupportNode('A03HCY', '123456')

app.conet.Idata.update({
    'mac':'fileserver'
})

app.extension(FilesNodes)

app.connect(('localhost', 1035), 'ASDF')

app.run()