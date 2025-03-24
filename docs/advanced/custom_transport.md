# Custom Transport Implementation

## Overview
Netcore allows implementation of any custom transport method by providing appropriate send and receive functions.

## Implementation Guide

### 1. Basic Requirements
- Receive function must accept size parameter
- Send function must accept data parameter
- Both functions must handle errors appropriately

### 2. Example Implementations

#### Custom Serial Protocol
```python
class CustomSerial:
    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.buffer = bytearray()
        
    def read(self, size):
        # Implement custom read logic
        pass
        
    def write(self, data):
        # Implement custom write logic
        pass

device = CustomSerial('/dev/custom0', 9600)
pipe = Pipe(device.read, device.write)
```

#### Network Protocol
```python
class CustomNetwork:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.connect()
        
    def receive(self, size):
        # Custom network receive
        pass
        
    def send(self, data):
        # Custom network send
        pass

net = CustomNetwork('localhost', 8080)
pipe = Pipe(net.receive, net.send)
```

### 3. Error Handling
```python
class RetryTransport:
    def read(self, size):
        retries = 3
        while retries > 0:
            try:
                return self.device.read(size)
            except Exception as e:
                retries -= 1
                if retries == 0:
                    raise e
                time.sleep(1)
``` 