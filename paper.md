---
title: 'Netcore: A Flexible Python Framework for Custom Protocol Communication'
tags:
  - Python
  - communication
  - network
  - protocol
  - framework
authors:
  - name: Yizhou Li
    orcid: 0009-0007-0924-4967
    affiliation: 1
affiliations:
  - name: Xiangxi Ethnic Middle School, Jishou, Hunan, China
    index: 1
date: 24 March 2025
---

# Summary

Communication protocols play a crucial role in modern software systems. While many mature communication protocols and frameworks exist, custom communication protocols are often required in specific scenarios. Netcore is a lightweight and extensible communication framework implemented in Python that provides flexible protocol encapsulation and communication management mechanisms. By abstracting the transport layer, it enables developers to implement any custom communication method while maintaining a consistent interface.

# Statement of need

When developing customized communication systems, developers face several challenges:

1. Implementing custom communication methods beyond standard protocols
2. Maintaining consistent interfaces across different transport mechanisms
3. Managing asynchronous data transmission and reception
4. Designing appropriate message routing and processing mechanisms

Existing communication frameworks typically focus on specific protocols or communication methods, lacking the flexibility to support arbitrary customization needs. The Netcore framework addresses these issues through layered design and unified interfaces:

- Provides reliable data serialization and transmission guarantees through `LsoProtocol`
- Abstracts transport methods through `Pipe`, allowing any custom communication implementation
- Offers high-level message routing and processing mechanisms through `Endpoint`

# Architecture

Netcore employs a three-layer architecture designed for maximum flexibility:

1. Protocol Layer (`LsoProtocol`):
   - Implements data packet serialization and deserialization
   - Supports large data chunking
   - Provides data integrity verification
   - Handles both memory and file-based storage

2. Transport Layer (`Pipe`):
   - Abstract interface for any communication method
   - Asynchronous queue management
   - Mission-based data transfer
   - Built-in error handling

3. Application Layer (`Endpoint`):
   - Message routing registration
   - Request-response management
   - Asynchronous callback handling
   - Global request context

# Features

1. Protocol Flexibility
   - Binary protocol with extensible headers
   - Support for JSON and raw data formats
   - Configurable chunk sizes for large data
   - Memory and file-based storage options

2. Universal Transport Layer
   - Abstract transport interface with send/receive functions
   - Asynchronous data transmission
   - Automatic message queuing
   - Support for any custom transport implementation

3. Error Handling
   - Standard logging system
   - Exception management
   - Data integrity checks
   - Thread safety mechanisms

# Implementation

A minimal example demonstrating the framework's usage:

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

This example shows how to:
1. Define custom transport functions
2. Set up the communication pipeline
3. Register message handlers
4. Start the service

# Availability

The source code is available at [https://github.com/A03HCY/Netcore](https://github.com/A03HCY/Netcore). Documentation can be found at [https://netcore.acdp.top](https://netcore.acdp.top). The software is released under the MIT license. 

# References