from acdpnet.nodes import ExtensionSupportNode
from acdpnet.extension.transfer import FilesNodes

app = ExtensionSupportNode('A03HCY', '123456')

app.connect(('localhost', 1035), 'ASDF')

app.send('activities')

print(app.recv())

app.send('multi_cmd', {
    'command':'ls',
    'remote':'fileserver'
})

print(app.recv())