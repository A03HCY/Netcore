from acdpnet.nodes import ExtensionSupportNode
from acdpnet.extension.transfer import FilesNodes

while True:
    app = ExtensionSupportNode('A03HCY', '')
    app.extension(FilesNodes)
    app.conet.Idata.update({
        'mac':'fs'
    })
    app.connect(('localhost', 1035), '')
    app.run()