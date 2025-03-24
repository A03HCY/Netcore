from .lso   import *
from typing import Any

class Response:
    def __init__(self, route:str, data:Any) -> None:
        pass

class Endpoint:
    def __init__(self, pipe:Pipe):
        self.pipe = pipe
    
    def start(self):
        self.pipe.start()
        
        