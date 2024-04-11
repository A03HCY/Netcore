from netcore import protocol as pt
from rich    import print
import io

pool = io.BytesIO()

data = pt.Protocol(extension='.example')
data.upmeta({
    'msg': [1, 2, 3]
})
data.create_stream(pool.write)

pool.seek(0)

recv = pt.Protocol()
recv.load_stream(pool.read)

print('[blue]Extn:', recv.extn)
print('[blue]Json:', recv.json)

'''
Extn: .example
Json:
{'msg': [1, 2, 3]}
'''