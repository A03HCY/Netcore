# Basic Examples

## TCP Server Example
```python
import socket
from netcore import Endpoint, Pipe

# Create TCP server socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('localhost', 8080))
server.listen(1)
conn, addr = server.accept()

# Define transport functions
def recv_func(size):
    return conn.recv(size)
    
def send_func(data):
    conn.send(data)

# Create endpoint
pipe = Pipe(recv_func, send_func)
endpoint = Endpoint(pipe)

# Register handlers
@endpoint.route("echo")
def handle_echo():
    return Response("echo", request.data)

endpoint.start()
```

## UART Example
```python
import serial
from netcore import Endpoint, Pipe

# Setup UART
ser = serial.Serial('/dev/ttyUSB0', 115200)

# Create endpoint
pipe = Pipe(
    lambda size: ser.read(size),
    lambda data: ser.write(data)
)
endpoint = Endpoint(pipe)

endpoint.start()
```

## Custom Protocol Example
```python
from netcore import Endpoint, Pipe

class CustomDevice:
    def read(self, size):
        # Your custom read implementation
        pass
        
    def write(self, data):
        # Your custom write implementation
        pass

device = CustomDevice()
pipe = Pipe(device.read, device.write)
endpoint = Endpoint(pipe)

endpoint.start()
``` 