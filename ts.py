import acdpnet.nodes as nd
import acdpnet.extension.transfer as tf



app = nd.BasicNode('A', 'A')

app.connect(('localhost', 1035), 'A')

tar = tf.RemoteFileSystem(app, '98:36:f5:63:fc:70-FileNode-9Mhk')

print(tar.listdir('./'))

print(tar.getcwd())

print(tar.path.isfile('./ts.py'))

with tar.open('./README.md', 'r', encoding='utf-8') as f:
    print(f.read(107))
    f.seek(0)
    f.save('./AAA.md')

