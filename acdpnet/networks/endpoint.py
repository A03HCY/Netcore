from acdpnet.protocol import *
import threading as td


class Reqst:
    def __init__(self):
        pass


class Endpoint:
    def __init__(self):
        self.ok = False
        self.func = {}
        self.__gene__()

    def __gene__(self):
        for n in dir(self):
            if not n.startswith('on_'): continue
            self.__regs__('.' + n[3:], getattr(self, n))

    def __regs__(self, extn, func, **options):
        self.func[extn] = [func, options]
        print('regs:', extn)

    def __hadl__(self):
        pass

    def route(self, extn, **options):
        if not extn[0] == '.': extn = '.' + extn
        def regsfunc(func):
            self.__regs__(extn, func, **options)
            return func
        return regsfunc
    
    def setnet(self, net:Acdpnet):
        self.net = net
        self.ok = True
    
    def run(self):
        if not self.ok: raise EnvironmentError('Network was not set')


class Terminal:
    def __init__(self):
        pass

