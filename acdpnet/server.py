if __name__ == '__main__':
    from acdpnet.services           import Tree
    from acdpnet.tools              import RanCode
    from acdpnet.extension.transfer import TransferSupport
    from rich.console               import Console
    from rich.prompt                import Prompt, IntPrompt

    class Prompt(Prompt):prompt_suffix = ''
    class IntPrompt(IntPrompt):prompt_suffix = ''

    console = Console()
    print  = console.print
    input  = Prompt.ask

    try:
        app =  Tree(input('Server Name : '))
        app.token = input('Server Token: ')
        port = IntPrompt.ask("Server Port : ")
        uses = {}
        stop = False
        print('Adding Group and its password. Type ".ext" to finish.')
        while not stop:
            name =  input('New Group   : ', console=console)
            if name == '.ext':
                stop = True
                break
            pwd  =  input('Password    : ', console=console, password=True)
            uses[name] = pwd
        if len(uses.keys()) == 0:
            print('Defult Group: "anyone"')
            pwd = RanCode(8)
            print('Defult Pwd  : "'+pwd+'"')
            uses['anyone'] = pwd
        elif len(uses.keys()) == 1:
            print('Updated 1 Group')
        else:
            print('Updated', len(uses.keys()), 'Groups')
        app.idf.acessuid.update(uses)
        app.extension(TransferSupport)
        print('[green3]Running at port' , port, '\n')
    except:pass

    try:
        app.run('0.0.0.0', port)
    except:
        print('Exit')