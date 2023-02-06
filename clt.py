import socket

from acdpnet import protocol as pt

sk = socket.socket()           

sk.connect(('127.0.0.1', int(input('# '))))

pt.setio(sk.recv, sk.send)


ds = pt.Acdpnet()

ds.push(pt.Protocol(meta=b'sg'))
ds.push(pt.Protocol(meta=b'wewe'))
ds.multi_send()

print('done')

sk.close()