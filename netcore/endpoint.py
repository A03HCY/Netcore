from  .protocol import Protocol, Package
import threading


class Request:
    def __init__(self, pak:Package, data:Protocol) -> None:
        self.__pakage = pak
        self.__is_ues = False
        self.__data   = data

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
    
    def response(self, extn, data) -> bool:
        if self.__is_ues: return False
        self.__pakage.send(Protocol(extension=extn).upmeta(data))
        self.__is_ues = True
        return True


class Endpoint:
    def __init__(self, sender, recver, buff:int=2048):
        self.__routes = {}
        self.__pakage = Package(sender=sender, recver=recver, buff=buff)
        self.send  = self.__pakage.send
        self.error = self.__pakage.error

    def start(self, thread=False):
        if self.__pakage.is_run: return
        self.__pakage.start()
        if not thread:
            while self.__pakage.is_run:
                self.__recv_handle()
        else:
            threading.Thread(target=self.__recv_handle).start()

    def route(self, extn):
        def decorator(func):
            self.__routes[extn] = func
            return func
        return decorator
    
    def __recv_handle(self):
        while self.__pakage.is_run:
            data = self.__pakage.recv()
            if data == None: break
            reqs = Request(self.__pakage, data)
            self.__handle_request(data.extn, reqs)
        self.__pakage.close()

    def __handle_request(self, extn, data):
        if extn in self.__routes:
            return self.__routes[extn](data)
        else:
            return '404 Not Found'