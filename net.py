import socket
from acdpnet import protocol as pt
from acdpnet.networks import endpoint as ep
import os

sk = socket.socket()
sk.bind(('127.0.0.1', int(input('# '))))
sk.listen()
conn, addr = sk.accept()

pt.setio(conn.recv, conn.send)

app = ep.Endpoint()
app.setnet(pt.Acdpnet())

@app.route('unknow')
def uk(data):
    print(data.meta.decode('utf-8'))

app.run()

'''
ds = pt.Acdpnet()

def a(data:pt.Protocol):
    print(str(data.meta.decode('utf-8')))
    return True

ds.recv_func = a
ds.recv_start(wait=True)
'''

conn.close()
sk.close()
