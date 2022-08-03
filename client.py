import acdpnet.nodes

app = nodes.BasicNode('A03HCY', '123456')

app.connect(('localhost', 1035), 'ASDF')

app.close()