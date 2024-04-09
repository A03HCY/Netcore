import socket
from core import endpoint as ep


sk = socket.socket()
sk.bind(('127.0.0.1', int(input('# '))))
sk.listen()
conn, addr = sk.accept()


end = ep.Endpoint(conn.send, conn.recv)

@end.route('.say')
def say(data:ep.Request):
    print(data.meta)

end.start()

conn.close()
sk.close()
