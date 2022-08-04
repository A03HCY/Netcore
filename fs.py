from acdpnet.nodes import ExtensionSupportNode
from acdpnet.extension.transfer import FilesNodes

app = ExtensionSupportNode('A03HCY', '')

app.conet.Idata.update({
    'mac':'fs'
})

app.extension(FilesNodes)

app.connect(('localhost', 1035), '')

app.run()