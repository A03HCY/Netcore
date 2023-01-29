from acdpnet.protocol import *

class DSTransfer:
    def __init__(self, read=None, write=None, extension:str='', encoding:str='utf-8') -> None:
        self.wt = gobwrite(write)
        self.rd = gobread(read)
        self.enco = encoding
        self.extn = extension
    
    def send(self, obj, extension:str='') -> None:
        self.send_obj(self.wt, obj, extesion=self.extn+extension, encoding=self.enco)
    
    def recv(self, extension:str=''):
        return self.recv_obj(self.rd, extesion=self.extn+extension, encoding=self.enco)

    @staticmethod
    def send_obj(func, obj, extesion:str='', encoding:str='utf-8') -> None:
        print(obj)
        meta = bytes(str(obj), encoding=encoding)
        ptcl = Protocol(meta, extension='.data_structure'+extesion)
        ptcl.create_stream(func)
    
    @staticmethod
    def recv_obj(func, extesion:str='', encoding:str='utf-8'):
        try:
            ptcl = Protocol.recv_stream_only(func=func, extension='.data_structure'+extesion)
            print(ptcl)
            if not ptcl:return None
        except:
            return 'stream_error'
        try:
            obj = literal_eval(ptcl.meta.decode(encoding=encoding))
            return obj
        except:return None


# Beta
class IOTransfer:
    def __init__(self, read=None, write=None, exit_with_error:bool=False) -> None:
        self.wt = gobwrite(write)
        self.rd = gobread(read)
        self.xt = exit_with_error
        self.ds = DSTransfer(self.wt, self.rd, extension='.io_transfer')
    
    def handle(self, func):
        while True:
            data = self.ds.recv('.data')
            if data == None:
                if self.xt:break
                continue
            if data == 'stream_error':break
            if data['cmd'] != 'execute':break
            target = getattr(func, data.get('method', '_None'), None)
            if not target:
                self.send_error(ModuleNotFoundError(data.get('method')+' is not exist'))
                continue
            if type(target) in [int, str, bytes, tuple, list]:
                data = {
                    'type':'result',
                    'result':target
                }
                self.ds.send(data, '.result')
                continue
            args = data['args']
            kwargs = data['kwargs']
            try:
                res = target(*args, **kwargs)
                data = {
                    'type':'result',
                    'result':res
                }
            except Exception as e:
                self.send_error(e)
                continue
            self.ds.send(data, '.result')
        
    def send_error(self, e):
        info = repr(e)
        data = {
            'type':'error',
            'error':info
        }
        self.ds.send(data, '.result')

    def local(self, func):
        self.ds.recv('.request')
        self.ds.send(dir(func), '.structure')
        self.handle(func)
    
    def open(self, exit=None):
        obj = IOTransfer.IObject(self.ds, exit)
        return obj

    @staticmethod
    class IObject:
        def __init__(self, ds:DSTransfer, exit=None):
            self.ds = ds
            self.ds.send({}, '.request')
            self.struct = self.ds.recv('.structure')
            self.ex = exit
            self.cd = False
            for i in self.struct:
                if '__' in i:continue
                setattr(self, i, self.__generate(i))

        def __generate(self, method_):
            def funcion(*args, **kwargs):
                data = {
                    'cmd':'execute',
                    'method':method_,
                    'args':args,
                    'kwargs':kwargs
                }
                self.ds.send(data, '.data')
                data = self.ds.recv('.result')
                print(data)
                if data['type'] == 'error':
                    self.__close()
                    self.cd = True
                    raise eval(data['error'])
                if data['type'] == 'result':
                    return data['result']
            return funcion

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            if not self.cd:self.__close()
        
        def __close(self):
            self.ds.send({'cmd':'exit'}, '.data')