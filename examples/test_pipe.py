from netcore.lso import Pipe
import socket

mode = input('Enter mode (server/client): ')

if mode == 'server':
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 8080))
    server.listen(5)
    print('Server started on port 8080')
    conn, addr = server.accept()
    print(f'Connected by {addr}')
    pipe = Pipe(conn.recv, conn.send)
    pipe.start()
    while True:
        if pipe.recv_pool:
            for key, value in pipe.recv_pool.items():
                print(key, value)
            pipe.recv_pool.clear()
            continue

if mode == 'client':
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 8080))
    pipe = Pipe(client.recv, client.send)
    pipe.start()
    while True:
        if pipe.recv_pool:
            for key, value in pipe.recv_pool.items():
                print(key, value)
            pipe.recv_pool.clear()
            continue
        data = input('Enter data to send: ')
        pipe.create_mission(data.encode('utf-8'))
