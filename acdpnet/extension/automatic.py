from acdpnet.tools import Conet
from io            import BytesIO
import pyautogui as pg
import ast

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