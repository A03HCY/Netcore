import acdpnet.nodes as nd
import acdpnet.extension.transfer as tf
import acdpnet.extension.automatic as at
from rich.console  import Console
from rich.prompt   import Prompt

class Prompt(Prompt):prompt_suffix = ''

console = Console()
print  = console.print
input  = Prompt.ask

app = nd.BasicNode('A', 'A')

app.connect(('localhost', 1035), 'A')

mc = '98:36:f5:63:fc:70-FileNode-4d9h'

tar = tf.RemoteFileSystem(app, mc)

print(tar.listdir('./'))

print(tar.path.isfile('./ts.py'))

ap2 = at.RemoteScreen(app, mc)

ap2.show()