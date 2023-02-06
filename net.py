import socket
from acdpnet import protocol as pt
import os

sk = socket.socket()
sk.bind(('127.0.0.1', int(input('# '))))
sk.listen()
conn, addr = sk.accept()


pt.setio(conn.recv, conn.send)
ds = pt.Acdpnet()

ds.multi_recv()

print(ds.list_rcv, ds.temp_rcv)


conn.close()
sk.close()
