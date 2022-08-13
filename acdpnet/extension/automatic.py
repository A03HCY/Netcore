from acdpnet.tools import *
from acdpnet.tools import Conet
from io            import BytesIO
from PIL           import Image
import pyautogui   as pg
import ast
import io

class ScreenNodes:
    description = {
        'screenprint':{
            'desc':'Screen print',
            'args':[{}],
            'resp':'Type:Dict'
        },
    }
    def screenprint(conet:Conet, meta=False):
        data = conet.get('data')
        temp = BytesIO()
        pg.screenshot().save(temp, format='JPEG')
        if meta:
            return temp.getvalue()
        data['resp'] = str(temp.getvalue())
        resp = {
            'command':'multi_cmd',
            'data':data
        }
        conet.sendata(resp)


class RemoteScreen(RemoteExtension):
    def show(self):
        self.send('screenprint')
        resp = self.node.recv(timeout=5)
        data = self.node.recv(timeout=5).get('data', {})
        
        temp = data.get('resp', '')
        if temp == '':
            print('❌ Not Support')
            return
        try:
            temp = ast.literal_eval(temp)
        except:
            print('❌ Cannot read')
            return
        if not type(temp) == bytes:
            print('❌ Cannot read')
            return
        temp = io.BytesIO(temp)
        temp = Image.open(temp)
        temp.show()