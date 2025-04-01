from netcore import Endpoint, EventEmitter, Blueprint, Pipe, MultiPipe, Response, request
import socket

# Blueprint test
blueprint = Blueprint(name='info', prefix='')

@blueprint.request('info')
def handle_info():
    # Get server's pipe safe_code
    return Response('info', {"status": "success", "safe_code": request.pipe_safe_code})

# EventEmitter test
event_emitter = EventEmitter()

@event_emitter.on('start')
def handle_start(*args, **kwargs):
    print('EventEmitter: Server started')

@event_emitter.on('request')
def handle_request(*args, **kwargs):
    print('EventEmitter: Request received', args, kwargs)

# Middleware test
def handle_middleware(func):
    print('Middleware received function:', func)
    return func

# Create TCP server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('localhost', 8080))
server.listen(5)
conn, addr = server.accept()

# MultiPipe test
pipe = Pipe(conn.recv, conn.send)
multi_pipe = MultiPipe()
multi_pipe.add_pipe(pipe)

endpoint = Endpoint(multi_pipe)
endpoint.register_blueprint(blueprint)
endpoint.middleware(handle_middleware)
endpoint.event = event_emitter

# Start service
endpoint.start()