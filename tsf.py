from acdpnet.nodes               import ExtensionSupportNode, GetMac
from acdpnet.tools               import RanCode
from acdpnet.extension.transfer  import FilesNodes
from acdpnet.extension.automatic import ScreenNodes
from rich.console                import Console
from rich.prompt                 import Prompt, IntPrompt
import time

class Prompt(Prompt):prompt_suffix = ''
class IntPrompt(IntPrompt):prompt_suffix = ''

console = Console()
print  = console.print
input  = Prompt.ask

def setup(self):
    print('Connected.')

try:
    ip    = 'localhost'
    token = ''
    port  = 1035
    uid   = 'A'
    pwd   = ''
except:pass


uni = RanCode(4)
app = ExtensionSupportNode(uid, pwd)
app.extension(FilesNodes)
app.extension(ScreenNodes)
app.conet.Idata.update({
    'mac':GetMac()+'-FileNode-'+uni
})
app.extension(FilesNodes)
app.extension(ScreenNodes)
app.setup = setup

try:
    app.connect((ip, port), token=token)
except:
    print('Failed to connect. Waiting for 30 sec.')

print(uni)
app.run()