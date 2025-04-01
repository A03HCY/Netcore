from netcore import Endpoint, Pipe, Response, request
import socket

# Connect to server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('localhost', 8080))

# Create pipe and endpoint
pipe = Pipe(client.recv, client.send)
endpoint = Endpoint(pipe)

# Start client (non-blocking)
endpoint.start(block=False)

# Get server's pipe safe_code
safe_code = endpoint.send('info', {"data": "safe_code"}, blocking_recv=True)
print('Assigned safe_code:', safe_code.json['safe_code'])

