from acdpnet.protocol import *


# Multi-threading is not supported because of single channel!
# Will use queuing to solve concurrency in the future version


class Reqst:
    def __init__(self):
        pass



class Endpoint:
    def __init__(self):
        self.__gene__()

    def __gene__(self):
        for n in dir(self):
            if not n.startswith('on_'): continue
            self.__regs__('.' + n[3:], getattr(self, n))

    def __regs__(self, extn, func, **options):
        self.__dict__[extn] = [func, options]
        print('regs:', extn)

    def __hadl__(self):
        extn, leng, meta = Protocol.parse_stream_head(self.rd)
        head, extn = Autils.chains(extn)
        if not head in self.__dict__: Protocol.ignore_stream(self.rd, from_head=meta)
        print('recv:', head)

    def route(self, extn, **options):
        if not extn[0] == '.': extn = '.' + extn
        def regsfunc(func):
            self.__regs__(extn, func, **options)
            return func
        return regsfunc
    
    def setio(self, read=None, write=None):
        self.rd = gobread(read)
        self.wt = gobwrite(write)
        self.ok = True
    
    def run(self):
        pass


class Terminal:
    def __init__(self):
        pass

