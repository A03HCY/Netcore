import socket
from acdpnet import transfer

sk = socket.socket()           

sk.connect(('127.0.0.1',8898))


d = transfer.IOTransfer(sk.send, sk.recv)
print('ok')

with d.open() as os:
    print(os.listdir('./'))

sk.close()