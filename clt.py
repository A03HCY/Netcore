import socket

from netcore import endpoint as pt

sk = socket.socket()           

sk.connect(('127.0.0.1', int(input('# '))))


pk = pt.Endpoint(sk.send, sk.recv, buff=2048)

@pk.route('.res')
def res(data:pt.Request):
    print(data.meta)

pk.start(thread=True)

while True:
    msg = input('> ')
    if msg == 'exit': break
    pk.send(pt.Protocol(extension='.say', meta=msg.encode('utf-8')))

pk.close()
sk.close()