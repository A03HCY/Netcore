import os
import sys
import shutil
import subprocess
import time
import importlib.util
import argparse

from rich.console  import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table    import Table
from rich          import box

# 设置一个环境变量标志，防止递归调用
if os.environ.get('NETCORE_BUILDING') == '1':
    print("检测到嵌套构建调用，退出...")
    sys.exit(1)

os.environ['NETCORE_BUILDING'] = '1'

# 创建Rich控制台
console = Console()

# 解析命令行参数
def parse_args():
    parser = argparse.ArgumentParser(description="Netcore构建脚本")
    parser.add_argument("-i", "--install", action="store_true", 
                        help="构建完成后安装包")
    return parser.parse_args()

# 动态获取版本号
def get_version():
    try:
        # 从__init__.py中导入__version__
        spec = importlib.util.spec_from_file_location("netcore", "netcore/__init__.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.__version__
    except Exception as e:
        console.print(f"[yellow]警告: 无法读取版本号: {e}[/yellow]")
        return "unknown"

def clean_build_dirs():
    """清理构建目录"""
    dirs_to_clean = ['build', 'dist', 'netcore.egg-info']
    
    with console.status("[bold cyan]清理构建目录...") as status:
        for dir_name in dirs_to_clean:
            if os.path.exists(dir_name):
                status.update(f"[bold cyan]删除 {dir_name}/")
                shutil.rmtree(dir_name)
                time.sleep(0.3)  # 添加短暂延迟以便看到状态变化

def build_package():
    """构建包"""
    # 创建DEVNULL对象用于隐藏输出
    DEVNULL = open(os.devnull, 'w')
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=True
    ) as progress:
        build_task = progress.add_task("[bold cyan]构建netcore包", total=100)
        
        try:
            # 更新进度和描述
            progress.update(build_task, advance=10, description="[bold cyan]准备构建环境")
            time.sleep(0.5)
            
            # 构建源码包
            progress.update(build_task, advance=20, description="[bold cyan]构建源码分发包 (tar.gz)")
            subprocess.check_call(
                [sys.executable, "setup.py", "sdist"],
                stdout=DEVNULL,
                stderr=subprocess.STDOUT
            )
            time.sleep(0.5)
            
            # 构建轮子包
            progress.update(build_task, advance=40, description="[bold cyan]构建轮子分发包 (whl)")
            subprocess.check_call(
                [sys.executable, "setup.py", "bdist_wheel"],
                stdout=DEVNULL,
                stderr=subprocess.STDOUT
            )
            
            # 完成 - 修复了空格问题
            progress.update(build_task, advance=30, description="[bold cyan]构建完成!")
            
            # 添加一个小延迟，确保进度条完成
            time.sleep(0.5)
        finally:
            # 确保关闭DEVNULL
            DEVNULL.close()

def install_package():
    """安装构建好的包"""
    console.print("\n[bold cyan]正在安装netcore包...[/bold cyan]")
    
    # 查找最新的wheel文件
    if not os.path.exists('dist'):
        console.print("[bold red]错误: 没有找到dist目录，无法安装[/bold red]")
        return False
    
    whl_files = [f for f in os.listdir('dist') if f.endswith('.whl')]
    if not whl_files:
        console.print("[bold red]错误: 没有找到wheel包，无法安装[/bold red]")
        return False
    
    # 按修改时间排序，选择最新的
    latest_whl = sorted(whl_files, 
                        key=lambda f: os.path.getmtime(os.path.join('dist', f)), 
                        reverse=True)[0]
    whl_path = os.path.join('dist', latest_whl)
    
    with console.status(f"[bold cyan]安装 {latest_whl}...") as status:
        try:
            # 使用pip安装wheel包，可能需要使用--force-reinstall以确保更新
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", whl_path, "--force-reinstall"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT
            )
            console.print(f"[bold green]✅ 成功安装 {latest_whl}[/bold green]")
            return True
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]❌ 安装失败: {e}[/bold red]")
            return False

def check_package():
    """检查构建的包"""
    
    if not os.path.exists('dist'):
        console.print("[bold red]错误: 没有找到dist目录，构建可能失败[/bold red]")
        return False
    
    files = os.listdir('dist')
    tar_gz_files = [f for f in files if f.endswith('.tar.gz')]
    whl_files = [f for f in files if f.endswith('.whl')]
    
    # 创建表格显示结果
    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED, title_justify="center")
    table.add_column("类型", style="dim", justify="center")
    table.add_column("文件名", style="dim", justify="center")
    table.add_column("状态", justify="center")
    
    if not tar_gz_files:
        table.add_row("源码", "无", "[bold red]缺失[/bold red]")
    else:
        for f in tar_gz_files:
            table.add_row("源码", f, "[bold green]✓[/bold green]")
        
    if not whl_files:
        table.add_row("轮子", "无", "[bold red]缺失[/bold red]")
    else:
        for f in whl_files:
            table.add_row("轮子", f, "[bold green]✓[/bold green]")
    
    console.print(table)
    
    return bool(tar_gz_files and whl_files)

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    # 获取版本
    version = get_version()
    
    # 使用分割线显示标题
    console.rule(f"[bold cyan]Netcore 构建脚本 v{version}[/bold cyan]")
    
    try:
        # 清理旧的构建目录
        clean_build_dirs()
        
        # 构建包
        build_package()
        
        # 检查构建结果
        build_success = check_package()
        
        if build_success:
            console.print("\n[bold green]✅ 构建成功! 分发包在 dist/ 目录下。[/bold green]")
            
            # 如果指定了安装选项，则安装包
            if args.install:
                install_success = install_package()
                if install_success:
                    console.print("\n[bold cyan]您可以现在导入netcore库进行测试。[/bold cyan]")
            
        else:
            console.print("\n[bold yellow]⚠️ 构建可能不完整，请检查上面的警告。[/bold yellow]")
            
    except KeyboardInterrupt:
        console.print("\n\n[bold red]❌ 构建被用户中断[/bold red]")
        return 130
    except subprocess.CalledProcessError as e:
        console.print(f"\n[bold red]❌ 构建过程出错: {e}[/bold red]")
        return 1
    except Exception as e:
        console.print(f"\n[bold red]❌ 发生错误: {e}[/bold red]")
        console.print_exception()
        return 1
        
    return 0

if __name__ == "__main__":
    exit_code = main()
    # 清除环境变量
    os.environ.pop('NETCORE_BUILDING', None)
    sys.exit(exit_code)