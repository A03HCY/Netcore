from .protocol import Protocol, Package
from .endpoint import Endpoint, get_request
import os

class FileSync(Endpoint):
    def on_listdir(self):
        request = get_request().json
        path = request['path']
        if os.path.isdir(path):
            return 'list', os.listdir(path)
        else:
            return 'list', []
    
    def on_isfile(self):
        request = get_request().json
        path = request['path']
        if not os.path.exists(path) or not os.path.isfile(path):
            return 'isfile', False
        return 'isfile', True
    
    def on_isdir(self):
        request = get_request().json
        path = request['path']
        if not os.path.exists(path) or not os.path.isdir(path):
            return 'isdir', False
        return 'isdir', True
    
    def on_info(self):
        request = get_request().json
        path = request['path']
        if not os.path.exists(path) or not os.path.isdir(path):
            return 'info', {}
        pass
        
    def on_sync(self):
        request = get_request().json
        path = request['path']
        seek = request['seek']
        buff = request['buff']