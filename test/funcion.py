class T:
    uio = 'yuyu'

    def __init__(self):
        data = ['a', 'b', 'c']
        for i in data:
            setattr(self, i, self.generate(i))
    
    def generate(self, name_):
        def funcion(*args, **kwargs):
            name = name_
            print(self.uio)
            print(args)
            print(kwargs)
            print(name)
        return funcion

print(type(T.generate))
