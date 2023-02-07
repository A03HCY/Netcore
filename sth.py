from acdpnet.protocol import *
from acdpnet.networks.endpoint import *

app = Endpoint(Acdpnet())

app.route('.hi')
def hi():
    pass

app.run()