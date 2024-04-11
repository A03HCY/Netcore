from netcore import protocol as pt
from rich    import print
import socket

inp = input('mode[s/c]:')

if inp == 's':
    print('[blue]Server mode')
    sk = socket.socket()
    sk.bind(('127.0.0.1', 5555))

    print('[blue]Listening')
    sk.listen()
    conn, addr = sk.accept()
    print('[green]Connected')

    pk = pt.Package(sender=conn.send, recver=conn.recv, buff=2048)
    pk.start()

    data = pk.recv()
    print('Recv:', data)

    pk.close()
    conn.close()
    sk.close()

if inp == 'c':
    print('[blue]Client mode')
    sk = socket.socket()
    sk.connect(('127.0.0.1', 5555))

    pk = pt.Package(sk.send, sk.recv)
    pk.start()
    msg = input('msg# ')
    pk.send(msg)

    pk.close()
    sk.close()