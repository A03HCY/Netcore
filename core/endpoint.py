from  .protocol import Protocol, Pakage
import threading


class Request:
    def __init__(self, pak:Pakage, data:Protocol) -> None:
        self.__pakage = pak
        self.__is_ues = False
        self.__data   = data

    @property
    def data(self):
        return self.__data

    @property
    def json(self):
        return self.__data.json

    @property
    def meta(self):
        return self.__data.meta
    
    def response(self, extn, data) -> bool:
        if self.__is_ues: return False
        self.__pakage.send(Protocol(extension=extn).upmeta(data))
        self.__is_ues = True
        return True


class Endpoint:
    def __init__(self, sender, recver, buff:int=2048):
        self.__routes = {}
        self.__pakage = Pakage(sender=sender, recver=recver, buff=buff)
        self.send = self.__pakage.send

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
            reqs = Request(self.__pakage, data)
            self.__handle_request(data.extn, reqs)

    def __handle_request(self, extn, data):
        if extn in self.__routes:
            return self.__routes[extn](data)
        else:
            return '404 Not Found'