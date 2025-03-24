# Quick Start

This guide will help you get started with Netcore quickly.

## Basic Usage

Here's a minimal example that demonstrates the core functionality:

```python
from netcore import Endpoint, Pipe

# Define custom transport functions
def recv_func(size): 
    return your_device.read(size)
    
def send_func(data):
    your_device.write(data)

# Create communication pipe
pipe = Pipe(recv_func, send_func)

# Create endpoint
endpoint = Endpoint(pipe)

# Register route handler
@endpoint.route("echo")
def handle_echo():
    return Response("echo", request.data)

# Start service
endpoint.start()
```

## Key Concepts

1. Transport Functions
   - Define how data is sent and received
   - Can be customized for any communication method

2. Pipe
   - Manages data transmission
   - Handles chunking and queuing

3. Endpoint
   - Provides routing system
   - Manages request/response lifecycle

## Next Steps

- Learn about [custom transport implementation](../advanced/custom_transport.md)
- Explore [error handling](../advanced/error_handling.md)
- Check the [API reference](../api/endpoint.md) 