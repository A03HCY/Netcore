import socket
from acdpnet import transfer
import os

sk = socket.socket()
sk.bind(('127.0.0.1', 8898))
sk.listen()

class T:
    tt = ['hi']

    def a(self, ss):
        print(ss)
    
    def b(self, s):return s

print('waiting')
conn, addr = sk.accept()
d = transfer.IOTransfer(conn.send, conn.recv)
print('ok')
d.local(os)

conn.close()
sk.close()
