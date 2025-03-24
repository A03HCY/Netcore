# Endpoint API

## Endpoint

### Constructor
```python
Endpoint(pipe: Pipe)
```

### Decorators
```python
@endpoint.route(route: str)
```
Register route handler

```python
@endpoint.default
```
Register default handler

### Methods
```python
def send(
    route: str,
    data: Any,
    callback: Optional[Callable] = None
) -> str
```
Send data to route with optional callback

```python
def send_response(
    data: Any,
    info: dict
) -> None
```
Send response to request

```python
def start(block: bool = True) -> None
```
Start endpoint

```python
def stop() -> None
```
Stop endpoint

## Request
Global request object with properties:
- `meta`: Raw bytes data
- `json`: JSON parsed data
- `string`: String decoded data

## Response
```python
Response(route: str, data: Any)
```
Response object for route handlers 