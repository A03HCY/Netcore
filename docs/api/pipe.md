# Pipe API

## Pipe

### Constructor
```python
Pipe(
    recv_function: Callable[[Optional[int]], bytes],
    send_function: Callable[[bytes], None]
)
```

### Properties
- `is_data` -> bool: Check if data available

### Methods
```python
def send(data: bytes, info: dict = {}) -> None
```
Send data with optional info

```python
def recv() -> tuple[bytes, dict]
```
Receive data and info

```python
def create_mission(
    data: bytes,
    info: dict = {},
    extension: Optional[str] = None,
    buff: int = 4096
) -> str
```
Create send mission

```python
def start() -> None
```
Start pipe threads 