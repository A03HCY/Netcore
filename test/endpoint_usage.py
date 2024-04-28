from netcore import endpoint as ep
from rich    import print
import socket

get_request = ep.get_request

inp = input('mode[s/c]:')

if inp == 's':
    sk = socket.socket()
    sk.bind(('0.0.0.0', 6666))
    sk.listen()
    conn, addr = sk.accept()

    end = ep.Endpoint(conn.send, conn.recv)

    @end.route('.say')
    def say():
        print(get_request())
        return ('.res', 'recved')

    end.start()

    conn.close()
    sk.close()

elif inp == 'c':
    sk = socket.socket()           
    sk.connect(('127.0.0.1', 6666))

    class rrr(ep.Endpoint):
        def on_res(self):
            print(get_request().code)

    rs = rrr(sk.send, sk.recv, buff=2048)
    rs.start(thread=True)

    while True:
        msg = input('> ')
        if msg == 'exit': break
        rs.send(ep.Protocol(extension='.say', meta=msg.encode('utf-8')))

    rs.close()
    sk.close()