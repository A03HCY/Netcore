from netcore import protocol as pt
from rich    import print
import socket

inp = input('mode[s/c]:')

if inp == 's':
    print('[blue]Server mode')
    sk = socket.socket()
    sk.bind(('0.0.0.0', 5555))
    sk.listen()
    conn, addr = sk.accept()

    print('[green]Connected')
    pk = pt.Package(sender=conn.send, recver=conn.recv, buff=2048)
    pk.start()

    while True:
        data = pk.recv()
        print('Recv:', data)

elif inp == 'c':
    print('[blue]Client mode')
    sk = socket.socket()
    sk.connect(('localhost', 5555))
    pk = pt.Package(sender=sk.send, recver=sk.recv, buff=2048)
    pk.start()

    while True:
        msg = input('msg# ')
        pk.send(msg)