# Netcore

[简体中文](README.md) | English

Netcore is a lightweight and extensible communication framework that provides flexible protocol encapsulation and communication management mechanisms. By abstracting the transport layer, it enables developers to implement any custom communication method while maintaining a consistent interface.

## Features

- Protocol Flexibility
  - Binary protocol with extensible headers
  - Support for JSON and raw data formats
  - Configurable chunk sizes for large data
  - Memory and file-based storage options

- Universal Transport Layer
  - Abstract transport interface
  - Asynchronous data transmission
  - Automatic message queuing
  - Support for any custom transport implementation

- Error Handling
  - Standard logging system
  - Exception management
  - Data integrity checks
  - Thread safety mechanisms

## Installation

```bash
pip install netcore
```

## Quick Start

Basic usage example:

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

## Documentation

For detailed documentation, visit [https://netcore.acdp.top](https://netcore.acdp.top)

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details. 