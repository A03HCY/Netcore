from rich.console  import Console, Group
from rich.progress import Progress, track, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.prompt   import Prompt, Confirm
from rich.panel    import Panel
from rich.table    import Column, Table
from rich          import box
from rich.tree     import Tree
from rich.pretty   import pprint
from acdpnet.nodes import ExtensionSupportNode
from acdpnet.tools import Conet, RemoteGet
from acdpnet       import extension
from PIL           import Image
import acdpnet
import platform
import os, sys, time
import ast, io
import matplotlib.pyplot as plt

class Prompt(Prompt):prompt_suffix = ''

console = Console()
print  = console.print
input  = Prompt.ask

def GetExtension():
    info = {}
    for i in dir(extension):
        if i.startswith('_'):continue
        info[i] = []
    for i in info:
        for ext in dir(getattr(extension, i)):
            if 'Nodes' in ext or 'Support' in ext:
                data = {}
                if 'description' in dir(getattr(getattr(extension, i), ext)):
                    data[ext] = getattr(getattr(getattr(extension, i), ext), 'description')
                else:
                    data[ext] = {}
                info[i].append(data)
    return info


class TreeExtension:
    def __init__(self, data:dict, title:str=None):
        self.data = data
        if not title:
            root = Tree("[bold]🗃️ Core Extension", highlight=True)
        else :
            root = Tree("[bold]🗃️ "+title, highlight=True)
        for filename in self.data.keys():
            fnode = root.add("📁 "+filename)
            for cla in data[filename]:
                claname = list(cla.keys())[0]
                cnode = fnode.add("📄 "+claname)
                for fun in cla[claname].keys():
                    funinfo = cla[claname][fun]
                    panel = Panel.fit(funinfo.get('desc', 'No Descr'))
                    uname = cnode.add(Group(fun, panel))
        self.root = root


class List:
    def __init__(self, path:str, data:list=[]):
        self.path = path
        self.table = Table(show_header=True, box=box.SIMPLE_HEAD)
        self.table.add_column("Name")
        self.table.add_column("Mode", justify="center")
        self.table.add_column("Last Time", justify="center")
        self.table.add_column("Size", justify="right", style="dodger_blue1")
        if path == '<data>':
            self.data(data)
        else:
            self.Do()
    
    def data(self, data):
        for i in data:
            self.table.add_row(
                i[0], i[1], i[2], i[3]
            )
    
    def Do(self):
        path  = os.path.abspath(self.path)
        dirs  = []
        files = []
        for i in os.listdir(path):
            full = os.path.join(path, i)
            if os.path.isdir(full):
                dirs.append(i)
            else:
                files.append(i)
        for i in dirs:
            p = os.path.join(path, i)
            self.table.add_row(
                "📁 "+i, oct(os.stat(p).st_mode)[-3:], self.time(p), '-'
            )
        for i in files:
            p = os.path.join(path, i)
            size = self.convert_size(os.path.getsize(p))
            self.table.add_row(
                "📄 "+i, oct(os.stat(p).st_mode)[-3:], self.time(p), size
            )
    
    def convert_size(self, text):
        units = [" B", "KB", "MB", "GB", "TB", "PB"]
        size = 1024
        for i in range(len(units)):
            if (text/ size) < 1:
                return "%.2f %s" % (text, units[i])
            text = text/ size
    
    def time(self, path):
        data = time.localtime(os.stat(path).st_mtime)
        return time.strftime("%Y-%m-%d %H:%M", data)


class Newmore:
    def __init__(self, conet:ExtensionSupportNode, info:dict):
        self.conet = conet
        self.info  = info
        self.mac   = self.info.get('mac')
        self.name  = self.conet.conet.get('uid')
        self.sname = self.info.get('name')
        self.meth  = self.info.get('meth')
        self.spath = ''
        self.console()
    
    def console(self):
        self.update()
        try:
            cmd = input('[green3]'+self.name+'@ [/green3][dodger_blue1]'+self.sname+'~'+self.spath.replace('\\', '/')+'[/dodger_blue1] [bold]$[/bold] ', console=console).split(' ')
            cmd.append('')
        except KeyboardInterrupt or UnboundLocalError:
            print('[bold red]Ctrl-C\nDisremote by "exit"')
            self.console()
            return
        
        if cmd[0] == 'clear':
            print("\033c", end="")
        elif cmd[0] == 'info':
            pprint(self.info, expand_all=True, console=console)
        elif cmd[0] == 'ls':
            self.ls(cmd)
        elif cmd[0] == 'cd':
            self.cd(cmd)
        elif cmd[0] == 'get':
            self.get(cmd)
        elif cmd[0] == 'screenprint':
            self.sprint(cmd)
        elif cmd[0] == 'extension':
            if cmd[1] == '-c':
                pprint(self.meth, expand_all=True, console=console)
            else:
                data = {
                    'Remote Node Services':[
                        {'AllSupport':self.meth}
                    ]
                }
                print(TreeExtension(data, 'Node Extension').root, '')
        elif cmd[0] == 'recv':
            num = 3
            if cmd[1].isnumeric():
                num = int(cmd[1])
            res = self.conet.conet.recvdata(timeout=num)
            pprint(res, expand_all=True, console=console)
        elif cmd[0] == 'exit':
            print('Disremoted from', self.sname, '\n')
            return
        else:
            self.handle(cmd)
        
        self.console()
    
    def send(self, cmd:str, data:dict={}):
        data['remote']  = self.mac
        data['command'] = cmd
        self.conet.send('multi_cmd', data)
    
    def update(self):
        self.send('pwd')
        resp = self.conet.recv()
        path = self.conet.recv().get('data', {}).get('resp', '')
        self.spath = path
    
    def cd(self, cmd):
        path = str(cmd[1])
        if path == '':path = './'
        data = {
            'path':path
        }
        self.send('cd', data=data)
        resp = self.conet.recv()
        data = self.conet.recv()
    
    def sprint(self, cmd):
        self.send('screenprint')
        resp = self.conet.recv()
        data = self.conet.recv(timeout=5).get('data', {})
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
    
    def get(self, cmd):
        name = str(cmd[1])
        if name == '':name = input('File: ')
        data = {
            'name':name
        }
        self.send('get', data=data)
        resp = self.conet.recv()
        data = self.conet.recv().get('data', {})
        print(data)
        if data.get('resp') != 'OK':
            print(data)
            return
        with open(os.path.join(os.getcwd(), name), 'wb') as f:
            print(os.path.join(os.getcwd(), name))
            target = RemoteGet(self.conet.conet).To(f)
            target.Now_Progress(console)
    
    def ls(self, cmd):
        path = str(cmd[1])
        if path == '':path = './'
        data = {
            'path':path
        }
        self.send('ls', data=data)
        resp = self.conet.recv()
        data = self.conet.recv().get('data', {}).get('resp', [])
        print(List('<data>', data=data).table)

    def handle(self, command):
        cmd = command[0]
        if not cmd in list(self.meth.keys()):
            print('Not Available')
            return
        args = self.meth[cmd].get('args', [{}])
        data = {}
        for i in args[0]:
            data[i] = input('[dodger_blue1]'+i+' : ', console=console)
        self.send(cmd, data)
        resp = self.conet.conet.recvdata()
        data = self.conet.conet.recvdata().get('data', {})
        if 'resp' in data:
            print(data['resp'])
        else:
            pprint(data, expand_all=True, console=console)

class Newclient:
    def __init__(self, name:str, ip:str, port:str):
        self.name = name
        self.ip   = ip
        self.port = port
        self.pwd  = ''
        self.token = ''
        self.sname = ''
        self.svers = ''
        self.meth  = {}
        self.conet = ExtensionSupportNode(self.name, self.pwd)
        if self.setup():self.start()
    
    def setup(self):
        print('Using Data : [green3]'+self.name+'@[/green3][dodger_blue1]'+self.ip+':[/dodger_blue1][dodger_blue1]'+self.port+'[/dodger_blue1]')
        gon = Confirm.ask("Creat")
        if not gon:return False
        return True
    
    def start(self):
        if not self.alive():
            print('❌ Service is not available\n')
            return
        else:
            tested = 1
            while tested <= 3:
                self.token = input('Token      : ', console=console, password=True)
                self.pwd = input('Password   : ', console=console, password=True)
                self.conet = ExtensionSupportNode(self.name, self.pwd)
                try:
                    self.conet.connect((self.ip, int(self.port)), self.token)
                    break
                except:pass
                print('🔒 Token or Passwork is not correct')
                if tested == 3:return
                tested += 1
        self.sname = self.conet.server.get('name', 'Unknow Server')
        self.svers = self.conet.server.get('version', 'Unknow Version')
        self.meth  = self.conet.server.get('meth', {})
        print('\n🟢 Service Version:', self.svers, '\tServer Name:', self.sname, '\n')
        self.console()
    
    def alive(self):
        Res = False
        try:
            self.conet.conet.connect((self.ip, int(self.port)))
            self.conet.conet.close()
            Res = True
        except:
            Res = False
        return Res

    def console(self):
        try:
            cmd = input('[green3]'+self.name+'@ [/green3][dodger_blue1]'+self.sname+'[/dodger_blue1] [bold]#[/bold] ', console=console).split(' ')
            cmd.append('')
        except KeyboardInterrupt or UnboundLocalError:
            print('[bold red]Ctrl-C\nDisconnect by "exit"')
            self.console()
            return

        if cmd[0] == 'clear':
            print("\033c", end="")
        elif cmd[0] == 'info':
            pprint(self.conet.server, expand_all=True, console=console)
        elif cmd[0] == 'extension':
            if cmd[1] == '-c':
                pprint(self.meth, expand_all=True, console=console)
            else:
                data = {
                    'Services':[
                        {'AllSupport':self.meth}
                    ]
                }
                print(TreeExtension(data, 'Server Extension').root, '')
        elif cmd[0] == 'exit':
            self.conet.close()
            print('Disconnected from', self.sname, '\n')
            return
        elif cmd[0] == 'recv':
            num = 3
            if cmd[1].isnumeric():
                num = int(cmd[1])
            res = self.conet.conet.recvdata(timeout=num)
            pprint(res, expand_all=True, console=console)
        elif cmd[0] == 'ls':
            self.lis(cmd)
        elif cmd[0] == 'conet':
            self.more(cmd)
        else:
            self.handle(cmd)

        self.console()
    
    def more(self, cmd):
        if not 'multi_cmd' in list(self.meth.keys()):
            print('Server Not Support\n')
            return
        mac = cmd[1]
        if not mac:
            mac = input('Target Mac: ')
        data = self.lis('', rd=True)
        info = {}
        for i in data:
            if i.get('mac') == mac:
                info = i
                break
        if info == {}:
            print('Error\n')
            return
        if info.get('meth', {}) == {}:
            print('Node Not Support\n')
            return
        try:
            Newmore(self.conet, info)
        except:
            print('[bold red]🔴 Disconnected from '+info.get('name', 'Remote Node')+'@'+info.get('mac', 'mac')+'\n')
    
    def lis(self, cmd, rd=False):
        if not 'activities' in list(self.meth.keys()):
            print('\nCommand Not Support')
            return
        self.conet.send('activities')
        data = self.conet.recv()
        if rd:return data
        if cmd[1] == '-c':
            pprint(data, expand_all=True, console=console)
        else:
            table = Table(show_header=True, box=box.SIMPLE_HEAD)
            table.add_column("Name", justify="center")
            table.add_column("OS", justify="center")
            table.add_column("Mac", justify="center")
            table.add_column("Version", justify="center", style="green3")
            table.add_column("Group", justify="center")
            table.add_column("Service Support", justify="center", style="dodger_blue1")
            for i in data:
                if i.get('meth', {}) == {}:
                    sp = False
                else:
                    sp = True
                table.add_row(
                    i.get('name'),
                    i.get('os'),
                    i.get('mac'),
                    i.get('version'),
                    i.get('uid'),
                    str(sp)
                )
            print(table)
    
    def handle(self, command):
        cmd = command[0]
        if not cmd in list(self.meth.keys()):
            print('Not Available')
            return
        args = self.meth[cmd].get('args', [{}])
        data = {}
        for i in args[0]:
            data[i] = input('[dodger_blue1]'+i+' : ', console=console)
        self.conet.send(cmd, data)
        resp = self.conet.conet.recvdata()
        if 'resp' in resp:
            print(resp['resp'])
        else:
            pprint(resp, expand_all=True, console=console)


class App:
    def __init__(self):
        self.name = platform.node()
        self.info()
        self.meth = {}

    def extension(self, ext):
        for name in dir(ext):
            if name == 'description':continue
            if name.startswith('_'):continue
            self.meth[name] = getattr(ext, name)
    
    def command(self, cmd:str='None'):
        def decorator(func):
            self.meth[cmd] = func
            return func
        return decorator
    
    def clear(self):
        print("\033c", end="")
    
    def info(self):
        self.clear()
        print('Core Version:', acdpnet.__version__)
        print('')
    
    def console(self):
        try:
            cmd = input('[green3]'+self.name+'@ [/green3][dodger_blue1]'+os.getcwd().replace('\\', '/')+'[/dodger_blue1] [bold]#[/bold] ', console=console).split(' ')
            cmd.append('')
        except KeyboardInterrupt or UnboundLocalError:
            print('[bold red]Ctrl-C\nExit by "exit"')
            self.console()
            return

        try:
            if cmd[0] in self.meth.keys():
                self.meth[cmd[0]](cmd[1:])
            else:pass
        except KeyboardInterrupt:
            print('[bold red]Canceled by user\n')
        
        '''
        if cmd[0] == 'ct':
            cmd = 'conet A03HCY@mhs.cool:1035'.split(' ')
            try:
                self.meth[cmd[0]](cmd[1:])
            except KeyboardInterrupt:
                print('[bold red]Canceled by user\n')
        '''
        
        if cmd[0] == 'clear':
            self.clear()
        if cmd[0] == 'exit':
            return
        elif cmd[0] == 're':
            try:
                os.system('python -m acdpnet')
            except KeyboardInterrupt:
                print('[bold red]Canceled by user\n')
            except:pass
        else:
            self.console()

class Command:
    def ls(data):
        path = str(data[0])
        if path == '':path = './'
        try:
            res = List(path)
            print(res.table)
        except:
            print('Path is not available')
    
    def cd(data):
        path = str(data[0])
        if path == '':path = './'
        try:os.chdir(path)
        except:pass
    
    def server(data):
        try:
            os.system('python -m acdpnet.server')
        except KeyboardInterrupt:
            print('[bold red]Canceled by user\n')
        except:
            print('Failed to start a server programe')
    
    def filenode(data):
        try:
            os.system('python -m acdpnet.filenode')
        except KeyboardInterrupt:
            print('[bold red]Canceled by user\n')
        except:
            print('Failed to start a server programe')
    
    def conet(data):
        args = data[0]
        name = ip = port = ''
        if '@' in args:
            name, args = args.split('@', 1)
        if ':' in args:
            ip, port = args.split(':', 1)
        else:
            ip = args
        if name == '':
            name = input('Group UID  : ')
        if ip   == '':
            ip = input('IP Address : ')
        if port == '':
            port = input('Remote Port: ')
        if not port.isnumeric():
            print('Remote Port Error\n')
            return
        try:
            Newclient(name, ip, port)
        except:
            print('[bold red]🔴 Disconnected from server\n')
    
    def extension(data):
        info = GetExtension()
        if data[0] == '-c':
            pprint(GetExtension(), expand_all=True, console=console)
        if data[0] == '':
            print(TreeExtension(info).root, '')
    
    def wget(data):
        extension.network.DownloadLocal(input('# '), console, buff=4096).start()
    
    def mv(data):
        pass



app = App()

app.extension(Command)

app.console()