# Application Layer (Endpoint)

## Overview
The Endpoint layer provides high-level message routing and request handling functionality.

## Core Features

### 1. Route Registration
- Decorator-based routing
- Pattern matching support
- Default route handling

### 2. Request Context
- Global request object
- Request metadata access
- Request lifecycle management

### 3. Response Handling
- Response formatting
- Callback support
- Error response handling

## Usage Examples

### Basic Routing
```python
from netcore import Endpoint, Response

@endpoint.route("hello")
def handle_hello():
    return Response("hello", "Hello World!")

@endpoint.route("echo")
def handle_echo():
    return Response("echo", request.data)
```

### With Callbacks
```python
def on_response(data, info):
    print(f"Received response: {data}")

endpoint.send("hello", "Hi!", callback=on_response)
```

### Default Handler
```python
@endpoint.default
def handle_default(data, info):
    print(f"Unhandled message: {data}")
``` 