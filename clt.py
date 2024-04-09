import socket

from core import protocol as pt

sk = socket.socket()           

sk.connect(('127.0.0.1', int(input('# '))))


pk = pt.Pakage(sk.send, sk.recv, buff=4)
pk.start()

while True:
    msg = input('> ')
    if msg == 'exit': break
    pk.send(pt.Protocol(extension='.say', meta=msg.encode('utf-8')))

pk.close()
sk.close()