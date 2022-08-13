from rich.console  import Console
from rich.progress import Progress
from urllib.parse  import unquote
import requests
import os
import time

def Hsize(size):
    def nchan(integer, remainder, level):
        if integer >= 1024:
            remainder = integer % 1024
            integer //= 1024
            level += 1
            return nchan(integer, remainder, level)
        else:
            return integer, remainder, level

    units = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB']
    integer, remainder, level = nchan(size, 0, 0)
    if level+1 > len(units):
        level = -1
    return ( '{}.{:>03d} {}'.format(integer, remainder, units[level]) )

def Getname(url, headers):
    filename = ''
    if 'Content-Disposition' in headers and headers['Content-Disposition']:
        disposition_split = headers['Content-Disposition'].split(';')
        if len(disposition_split) > 1:
            if disposition_split[1].strip().lower().startswith('filename='):
                file_name = disposition_split[1].split('=')
                if len(file_name) > 1:
                    filename = unquote(file_name[1])
    if not filename and os.path.basename(url):
        filename = os.path.basename(url).split("?")[0]
    if not filename:
        return time.time()
    return filename

class DownloadLocal:
    headers = {'user-agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
    def __init__(self, url, con, path='./', buff=1024):
        self.url = url
        self.con = con
        self.path = path
        self.buff = buff
        self.pasa = True
        try:self.init()
        except:
            self.con.print('[bold red]Connect Failed')
            self.pasa = False
    
    def init(self):
        self.req = requests.get(self.url, stream=True, headers=self.headers)
        self.size = int(self.req.headers.get('Content-Length', '-1'))
        self.name = Getname(self.url, self.req.headers)
        if len(self.name) >= 260:
            self.name = 'Down.cots'
        # --- print info --- #
        self.con.print('[bold]Name : ', end='')
        self.con.print('[bold dodger_blue1]'+ self.name)
        if self.size != -1:
            self.con.print('[bold]Size : ', end='')
            self.con.print('[bold dodger_blue1]'+ Hsize(self.size))

    def do(self):
        from rich.console  import Console, Group
        from rich.progress import Progress
        from rich.progress import (
            BarColumn,
            DownloadColumn,
            Progress,
            SpinnerColumn,
            TaskProgressColumn,
            TimeElapsedColumn,
            TimeRemainingColumn,
            TransferSpeedColumn,
        )
        cope = os.path.join(self.path, self.name + '.cope')
        sture = os.path.join(self.path, self.name)
        stall = 0
        mode = 'wb'
        name = self.name
        with Progress(
            SpinnerColumn(),
            "{task.description}",
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.con,
        ) as progress:
            # temp file
            if os.path.exists(cope):
                stall = os.path.getsize(cope)
                self.con.print('[bold yellow]Restart from Temp File: [bold green3]' + Hsize(stall))
                mode = 'ab'
                headers={'Range': 'bytes=%d-' %stall }
                self.req = requests.get(self.url,stream=True)
                if int(self.req.headers.get('Content-Length', '-1')) != self.size:
                    self.con.print('[bold red]Reload Failed.')
                    mode = 'wb'
                    stall = 0
            # create progress
            task = progress.add_task('[bold dodger_blue1]Copy.', total=self.size+1)
            progress.update(task, advance=stall)
            # download
            ticks = time.time()
            stu = stall
            with open(cope, mode) as f:
                for chunk in self.req.iter_content(chunk_size=self.buff):
                    length = len(chunk)
                    if chunk:
                        f.write(chunk)
                        stall += length
                    if time.time() - ticks >= 0.5:
                        ticks = time.time()
                        progress.update(task, advance=(stall-stu))
                        stu = stall
                progress.update(task, advance=(stall-stu))
            # rename
            num = 1
            while True:
                try:
                    os.rename(cope, sture)
                    break
                except:pass
                filename,extension = os.path.splitext(self.name)
                name = filename + ' ('+str(num)+')' + extension
                sture = os.path.join(self.path, name)
                num += 1
            progress.update(task, advance=1)
        self.con.print('[bold green3]Download '+name+' Successfully.')
    
    def unkn(self):
        cope = os.path.join(self.path, self.name + '.cope')
        sture = os.path.join(self.path, self.name)
        mode = 'wb'
        name = self.name
        # download
        with open(cope, mode) as f:
            with console.status('[bold dodger_blue1]Copy...[/]'):
                for chunk in self.req.iter_content(chunk_size=self.buff):
                    if chunk:
                        f.write(chunk)
        # rename
        num = 1
        while True:
            try:
                os.rename(cope, sture)
                break
            except:pass
            filename,extension = os.path.splitext(self.name)
            name = filename + ' ('+str(num)+')' + extension
            sture = os.path.join(self.path, name)
            num += 1
        self.con.print('[bold]Size : ', end='')
        self.con.print('[bold dodger_blue1]'+ Hsize(os.path.getsize(sture)))
        self.con.print('[bold green3]Download '+name+' Successfully.')
    
    def start(self):
        if not self.pasa:return
        try:
            if self.size != -1:
                self.do()
            else:
                self.unkn()
        except KeyboardInterrupt:
            self.con.print('[bold red]User Exit.')
        except OSError:
            self.con.print('[bold red]Memory Not Available.')