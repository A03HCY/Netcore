import socket
from acdpnet import protocol as pt
import os

sk = socket.socket()
sk.bind(('127.0.0.1', int(input('# '))))
sk.listen()
conn, addr = sk.accept()

pt.setio(conn.recv, conn.send)
ds = pt.Acdpnet()

def a(data:pt.Protocol):
    print(str(data.meta.decode('utf-8')))
    return True

ds.func = a
ds.recv_start(wait=True)

conn.close()
sk.close()
