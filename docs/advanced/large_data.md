# Large Data Transfer

## Overview
Netcore provides built-in support for handling large data transfers efficiently.

## Features

### 1. Automatic Chunking
- Configurable chunk size
- Progress tracking
- Memory efficient

### 2. Storage Options
- Memory-based for small data
- File-based for large data
- Hybrid mode support

## Implementation

### Memory Mode
```python
from netcore import LsoProtocol

# Default memory mode
lso = LsoProtocol()
lso.set_meta(large_data)
```

### File Mode
```python
# File mode for large data
lso = LsoProtocol(local="large_data.bin")
lso.set_meta(large_data)
```

### Chunked Transfer
```python
# Configure chunk size
pipe = Pipe(recv_func, send_func)
pipe.create_mission(large_data, buff=8192)
``` 