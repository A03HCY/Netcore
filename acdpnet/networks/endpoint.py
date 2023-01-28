from acdpnet.protocol import *


class Reqst:
    def __init__(self):
        pass


request = Reqst()


class Autils:
    @staticmethod
    def chains(extn):
        data = extn[1:].split('.')
        head = data[0]
        extn = '.' + '.'.join(data[1:])
        return head, extn


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
    
    def setio(self, read, write):
        self.rd = read
        self.wt = write
        self.ok = True
    
    def run(self):
        pass