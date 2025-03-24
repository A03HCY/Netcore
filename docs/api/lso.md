# LSO Protocol API

## LsoProtocol

### Constructor
```python
LsoProtocol(local: Optional[str] = None, encoding: str = 'utf-8', buff: int = 2048)
```

### Properties
- `length` -> int: Get current meta data length
- `meta` -> bytes: Get meta data
- `json` -> dict: Get meta data as JSON
- `extension` -> str|bytes: Get/set extension
- `head` -> bytes: Get protocol header

### Methods
```python
def set_meta(data: Union[bytes, bytearray, str]) -> None
```
Set meta data

```python
def full_data(buff: Optional[int] = None) -> Generator
```
Generate complete data stream

```python
def load_stream(
    function: Callable,
    head: Optional[Union[bytes, bytearray]] = None,
    handler: Optional[Callable] = None,
    buff: Optional[int] = None
) -> 'LsoProtocol'
```
Load data from stream

```python
def load_generator(
    generator: Generator,
    extension: Optional[str] = None,
    handler: Optional[Callable] = None,
    set_length: bool = True
) -> 'LsoProtocol'
```
Load data from generator 