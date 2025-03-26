from netcore import Endpoint, Pipe, Response, request
from netcore.endpoint import logger
import socket
import logging


# Create TCP server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('localhost', 8080))
server.listen(5)
conn, addr = server.accept()

# Create pipe and endpoint
pipe = Pipe(conn.recv, conn.send)
endpoint = Endpoint(pipe)

# Register handlers for concurrent messages
@endpoint.request('message1')
def handle_message1():
    print(request.route, request.json)
    # This handler can run while other messages are being processed
    return Response('message1', {"status": "processed"})

@endpoint.request('message2')
def handle_message2():
    # Another concurrent handler
    return Response('message2', {"status": "processed"})

# Start service
endpoint.start()