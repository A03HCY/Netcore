from  .protocol import Protocol, Package
import threading
import contextvars

class Request:
    def __init__(self, data:Protocol) -> None:
        self.__data = data

    @property
    def code(self) -> str:
        return self.__data.code

    @property
    def data(self) -> Protocol:
        return self.__data

    @property
    def json(self) -> dict:
        return self.__data.json

    @property
    def meta(self) -> bytes:
        return self.__data.meta

_request = contextvars.ContextVar('request', default=Request(Protocol()))

def set_request(data):
    _request.set(Request(data))

def get_request():
    return _request.get()

class Endpoint:
    def __init__(self, sender, recver, buff:int=2048):
        self.__routes = {}
        self.__pakage = Package(sender=sender, recver=recver, buff=buff)
        self.send  = self.__pakage.send
        self.error = self.__pakage.error

    def start(self, thread=False):
        if self.__pakage.is_run: return
        self.__reg_function()
        self.__pakage.start()
        if not thread:
            while self.__pakage.is_run:
                self.__recv_handle()
        else:
            threading.Thread(target=self.__recv_handle).start()
    
    def send_pack(self, extn, meta=None):
        self.__pakage.send(Protocol(extension=extn).upmeta(meta))

    def route(self, extn):
        def decorator(func):
            self.__routes[extn] = func
            return func
        return decorator
    
    def __reg_function(self):
        members = dir(self)
        for member in members:
            if member.startswith("on_") and callable(getattr(self, member)):
                print('reg', getattr(self, member))
                self.__routes[member[3:]] = getattr(self, member)
    
    def __recv_handle(self):
        while self.__pakage.is_run:
            data = self.__pakage.recv()
            if data == None: break
            set_request(Request(data))
            result = self.__handle_request(data.extn)
            if type(result) in [list, tuple] and len(result) == 2:
                self.__pakage.send(Protocol(extension=result[0]).upmeta(result[1]))
            if type(result) == Protocol:
                self.__pakage.send(result)
        self.__pakage.close()

    def __handle_request(self, extn:str):
        if extn in self.__routes:
            return self.__routes[extn]()
        elif extn.startswith('.') and extn[1:] in self.__routes:
            return self.__routes[extn[1:]]()
        else:
            return '.handle_error', 'not found'