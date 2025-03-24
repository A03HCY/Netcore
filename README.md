# Netcore

[![status](https://joss.theoj.org/papers/08b1c73b184c1341f51e01ee052647ae/status.svg)](https://joss.theoj.org/papers/08b1c73b184c1341f51e01ee052647ae) ![PyPI - Version](https://img.shields.io/pypi/v/netcore?label=PyPI&color=green)

English | [简体中文](README_zh.md) 

Netcore is a lightweight communication framework that enables concurrent message transmission over a single connection. By implementing a message chunking and scheduling mechanism similar to CPU time-slicing, it allows multiple messages to be sent and received simultaneously without establishing multiple connections.

## Core Features

- Concurrent Message Transmission
  - Single connection handles multiple concurrent messages
  - Automatic message chunking and reassembly
  - Message scheduling and prioritization
  - Non-blocking message transmission

- Smart Message Management
  - Unique message ID tracking
  - Automatic message queuing
  - Message priority handling
  - Message completion verification

- Protocol Layer
  - Binary protocol with message chunking
  - Support for JSON and raw data formats
  - Configurable chunk sizes
  - Memory and file-based storage options

- Transport Layer Abstraction
  - Universal transport interface
  - Asynchronous data transmission
  - Thread safety mechanisms
  - Custom transport support

## Advanced Features

- Blueprint System
  - Route grouping and prefixing
  - Modular application structure
  - Middleware support at blueprint level
  - Isolated error handling per blueprint

- Event System
  - Event subscription and publishing
  - One-time event handlers
  - System event monitoring
  - Asynchronous event processing

- Task Scheduler
  - Delayed task execution
  - Periodic task scheduling
  - Priority-based scheduling
  - Thread-safe task management

- Cache System
  - In-memory caching
  - TTL (Time-To-Live) support
  - Automatic cache cleanup
  - Thread-safe operations

## Quick Start

### Server Example

```python
from netcore import Endpoint, Pipe, Response, request
import socket

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
    # This handler can run while other messages are being processed
    return Response('message1', {"status": "processed"})

@endpoint.request('message2')
def handle_message2():
    # Another concurrent handler
    return Response('message2', {"status": "processed"})

# Start service
endpoint.start()
```

### Client Example

```python
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
endpoint.send('message1', {"data": "First message"})
endpoint.send('message2', {"data": "Second message"})
# Both messages will be processed concurrently
```

## Advanced Usage Examples

### Blueprint Example
```python
from netcore import Endpoint, Blueprint, Response, request

# Create a blueprint for user-related routes
user_bp = Blueprint("users", "/user")

@user_bp.request("/list")
def user_list():
    return Response("/user/list", {"users": ["user1", "user2"]})

# Register blueprint to endpoint
endpoint.register_blueprint(user_bp)
```

### Event System Example
```python
# Subscribe to events
@endpoint.event.on('start')
def on_start():
    print("Service started")

# One-time event
@endpoint.event.once('initialize')
def on_init():
    print("First-time initialization")

# Emit events
endpoint.event.emit('custom_event', data={"type": "notification"})
```

### Task Scheduler Example
```python
# Schedule periodic task
def periodic_check():
    print("Performing periodic check")

endpoint.scheduler.schedule(periodic_check, delay=5, interval=60)  # Run every 60s after 5s delay
```

### Cache System Example
```python
# Cache expensive operations
@endpoint.request('/data')
def get_data():
    # Try to get from cache
    data = endpoint.cache.get("expensive_data")
    if data is None:
        # Compute and cache for 5 minutes
        data = compute_expensive_data()
        endpoint.cache.set("expensive_data", data, ttl=300)
    return Response("/data", data)
```

## How It Works

1. **Message Chunking**: Large messages are automatically split into smaller chunks
2. **Concurrent Processing**: Each message is processed independently
3. **Scheduling**: Chunks from different messages are interleaved for efficient transmission
4. **Reassembly**: Message chunks are automatically reassembled at the destination

## Documentation

For detailed documentation, visit [https://netcore.acdp.top](https://netcore.acdp.top)

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details. 