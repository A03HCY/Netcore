def init():
    global _ds
    _ds = {}

def set(key, value): _ds[key] = value

def get(key, df=None): return _ds.get(key, df)

def items(): return _ds.items()

def keys(): return _ds.keys()

def pop(key): return _ds.pop(key)

def clear(): _ds.clear()

def setdefault(key): return _ds.setdefault(key)

def setlist(keys):
    for i in keys: _ds.setdefault(i)