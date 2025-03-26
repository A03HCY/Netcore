# Netcore

[![JOSS Paper](https://joss.theoj.org/papers/08b1c73b184c1341f51e01ee052647ae/status.svg)](https://joss.theoj.org/papers/08b1c73b184c1341f51e01ee052647ae) ![PyPI - Version](https://img.shields.io/pypi/v/netcore?label=PyPI&color=green) ![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

English | [简体中文](README_zh.md) 

Netcore is a lightweight communication framework specifically designed for **concurrent message transmission within a single connection**. Through innovative message chunking and scheduling mechanisms, it enables simultaneous processing of multiple message streams without establishing multiple connections, significantly improving communication efficiency in resource-constrained scenarios.

## Core Features

### 🚀 Concurrent Transmission Engine
• **Single-connection multiplexing**: Implements logically concurrent message streams on a single physical connection
• **Intelligent chunk scheduling**: Automatically splits large messages into chunks for interleaved transmission, maximizing bandwidth utilization
• **Non-blocking I/O**: Decouples message transmission from business processing to ensure system responsiveness

### 📦 Protocol & Transport
• **Adaptive protocol layer**:
  • Supports binary/JSON/raw data formats
  • Configurable chunk size (default 4KB)
  • Hybrid memory-file storage mode
• **Transport abstraction interface**:
  • Compatible with any I/O devices (serial/TCP/Bluetooth/etc.)
  • Provides dual-mode synchronous/asynchronous APIs
  • Thread-safe message queue management

### 🧩 Enterprise-grade Capabilities
• **Blueprint system**:
  • Modular routing groups (supports prefixes and nesting)
  • Blueprint-level middleware and error handling
  • Hot-swappable component registration
• **Event hub**:
  • Publish-subscribe pattern
  • One-time event binding
  • System lifecycle event monitoring (startup/shutdown/error)
• **Task scheduler**:
  • Millisecond-level timing tasks
  • Adaptive priority queues
  • Failed task retry mechanism
• **Smart caching**:
  • LRU memory cache
  • TTL auto-expiration
  • Cache penetration protection
  • Thread-safe access

## Installation

```bash
pip install netcore
```

**System Requirements**:
• Python ≥ 3.8
• No external dependencies (pure standard library implementation)

## Quick Start

### Basic Example: Serial Communication
```python
from netcore import Endpoint, Pipe
import serial

# Initialize serial device
ser = serial.Serial('/dev/ttyUSB0', 115200)

# Create communication pipe (only requires read/write functions)
pipe = Pipe(ser.read, ser.write)
endpoint = Endpoint(pipe)

# Register message handler
@endpoint.request('sensor_data')
def handle_sensor():
    return Response('sensor_ack', {"status": "OK"})

# Start service (default 4 worker threads)
endpoint.start()
```

## Architecture Overview

1. **Application Layer (Endpoint)**  
   • Routing system: Handles message routing and blueprint registration
   • Event system: Implements publish-subscribe event hub
   • Task system: Manages scheduled tasks and priority queues
   • Cache system: Provides thread-safe LRU caching

2. **Transport Layer (Pipe)**  
   • Send queue: Implements priority task queue management
   • Receive pool: Maintains temporary and complete message storage
   • Thread locks: Ensures thread-safe access to shared resources
   • Protocol integration: Deep integration with LsoProtocol for chunked transmission

3. **Protocol Layer (LsoProtocol)**  
   • Intelligent chunking: Auto-selects memory/file storage based on data type
   • Metadata management: Maintains extended headers and message integrity checks
   • Hybrid storage: Enables seamless switching between memory buffers and persistent files

4. **Concurrency Model**  
   • Main thread: Handles I/O monitoring and request queuing
   • Worker thread pool: Processes requests independently from queue
   • Thread isolation: Achieves request context isolation through thread-local storage

5. **Data Flow**  
   • Bidirectional channel: Demonstrates complete loop from application layer to physical devices
   • Protocol transparency: Completely hides serialization/deserialization from upper layers
   • Asynchronous processing: Decouples non-blocking transmission from business logic

## Documentation & Support

📚 [Full Documentation](https://netcore.acdp.top) | 💬 [Community Discussions](https://github.com/A03HCY/Netcore/discussions) | 🐛 [Issue Tracker](https://github.com/A03HCY/Netcore/issues)

Documentation includes:
• API Reference Manual
• Architecture White Paper
• Best Practice Guide
• Performance Optimization Tips

## Contribution Guide

We welcome contributions through:
1. Code improvements via Pull Requests
2. Documentation enhancements or translations
3. Test case submissions
4. Security vulnerability reports

## License

[MIT License](LICENSE)