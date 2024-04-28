from .protocol import Protocol, Package
from .endpoint import Endpoint, get_request
import os

class FileSync(Endpoint):
    def on_listdir(self):
        request = get_request()
        return 'list', os.listdir()
    