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

# Send multiple messages concurrently
print(endpoint.send('message1', {"data": "First message"}, blocking_recv=True))
print(endpoint.send('message2', {"data": "Second message"}, blocking_recv=True))
# Both messages will be processed concurrently