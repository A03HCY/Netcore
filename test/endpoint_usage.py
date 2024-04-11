from netcore import endpoint as ep
from rich    import print
import socket

inp = input('mode[s/c]:')

if inp == 's':
    sk = socket.socket()
    sk.bind(('0.0.0.0', 6666))
    sk.listen()
    conn, addr = sk.accept()

    end = ep.Endpoint(conn.send, conn.recv)

    @end.route('.say')
    def say(data:ep.Request):
        print(data.code)
        data.response('.res', 'recved')

    end.start()

    conn.close()
    sk.close()

elif inp == 'c':
    sk = socket.socket()           
    sk.connect(('127.0.0.1', 6666))

    pk = ep.Endpoint(sk.send, sk.recv, buff=2048)

    @pk.route('.res')
    def res(data:ep.Request):
        print(data.code)

    pk.start(thread=True)

    while True:
        msg = input('> ')
        if msg == 'exit': break
        pk.send(ep.Protocol(extension='.say', meta=msg.encode('utf-8')))

    pk.close()
    sk.close()