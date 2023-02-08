import socket

from acdpnet import protocol as pt

sk = socket.socket()           

sk.connect(('127.0.0.1', int(input('# '))))

pt.setio(sk.recv, sk.send)


#ds = pt.Acdpnet()

while True:
    msg = input('> ')
    if msg == 'exit': break
    pt.send(pt.Protocol(meta=msg.encode('utf-8')))
    #ds.singl_push(pt.Protocol(meta=msg.encode('utf-8')))
    #ds.singl_send()

sk.close()