from netcore.lso import Pipe
from netcore.endpoint import Endpoint, request, Response

pipe = Pipe()
endpoint = Endpoint(pipe)

@endpoint.request('test')
def test():
    print(request.data)

@endpoint.request('test2')
def test2():
    print(request.data)
    data = {
        'msg': 'hello'
    }
    return Response('res', data)

endpoint.start()
