if __name__ == '__main__':
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
        ip    = input('Server IP   : ')
        token = input('Server Token: ')
        port  = IntPrompt.ask("Server Port : ")
        uid   = input('Group Name  : ')
        pwd   = input('Password    : ')
    except:pass

    while True:
        app = ExtensionSupportNode(uid, pwd)
        app.extension(FilesNodes)
        app.extension(ScreenNodes)
        app.conet.Idata.update({
            'mac':GetMac()+'-FileNode-'+RanCode(4)
        })
        app.extension(FilesNodes)
        app.extension(ScreenNodes)
        app.setup = setup

        try:app.connect((ip, port), token=token)
        except:
            print('Failed to connect. Waiting for 30 sec.')
            time.sleep(30)
            continue
        
        try:app.run()
        except:pass