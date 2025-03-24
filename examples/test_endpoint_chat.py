from netcore.lso import Pipe
from netcore.endpoint import Endpoint, Response, request
import socket
import json
import time

mode = input('模式 (s=服务器/c=客户端): ').lower()

def print_data(prefix, data, info=None):
    """简化的数据打印函数"""
    print(f"\n==={prefix}===")
    if info:
        print(f"消息ID: {info.get('message_id', '')}")
        print(f"路由: {info.get('route', '')}")
    
    if isinstance(data, (bytes, bytearray)):
        try:
            content = data.decode('utf-8')
            try:
                json_data = json.loads(content)
                print(f"内容: {json_data}")
            except:
                print(f"内容: {content}")
        except:
            print(f"内容: [二进制数据]")
    else:
        print(f"内容: {data}")
    print("===========")

def handle_response(data, info):
    """通用响应处理函数"""
    print_data("收到响应", data, info)

if mode.startswith('s'):
    # 服务器模式
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 8080))
    server.listen(5)
    print('服务器启动在端口 8080，等待客户端连接...')
    conn, addr = server.accept()
    print(f'客户端 {addr} 已连接')
    
    pipe = Pipe(conn.recv, conn.send)
    endpoint = Endpoint(pipe)
    
    @endpoint.request('echo')
    def handle_echo():
        print(request.meta)
        message = request.json.get('message', '')
        print_data("收到echo请求", request.json)
        return Response('echo', {"reply": f"服务器回声: {message}"})
    
    @endpoint.default
    def handle_default(data, info):
        print_data("收到未知请求", data, info)
        try:
            text = data.decode('utf-8') if isinstance(data, bytes) else str(data)
            endpoint.send_response({"status": "ok", "message": f"已收到: {text[:20]}..."}, info)
        except:
            endpoint.send_response({"status": "ok"}, info)
    
    endpoint.start(block=False)
    print("服务器已启动，输入消息发送到客户端，输入'q'退出")
    
    try:
        while True:
            cmd = input("\n> ")
            if cmd.lower() == 'q':
                break
            
            message_id = endpoint.send('server_msg', {"text": cmd, "time": time.time()}, handle_response)
            print(f"已发送，ID: {message_id}")
            
    except KeyboardInterrupt:
        print("\n正在关闭...")
    

elif mode.startswith('c'):
    # 客户端模式
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 8080))
    print('已连接到服务器')
    
    pipe = Pipe(client.recv, client.send)
    endpoint = Endpoint(pipe)
    
    @endpoint.request('server_msg')
    def handle_server_msg():
        message = request.json.get('text', '')
        print_data("收到服务器消息", message)
        return Response('client_reply', {"status": "received"})
    
    @endpoint.request('echo')
    def handle_echo():
        print("原始请求数据:", request.meta)
        print("JSON数据:", request.json)
        reply = request.json.get('reply', '无回复')
        print_data("收到回声响应", reply)
        return None
    
    @endpoint.default
    def handle_default(data, info):
        print_data("收到未知消息", data, info)
        endpoint.send_response({"status": "received"}, info)
    
    endpoint.start(block=False)
    print("客户端已启动，可用命令: echo <消息>, q(退出)")
    print(endpoint.routes)
    
    try:
        while True:
            cmd = input("\n> ")
            if cmd.lower() == 'q':
                break
                
            if cmd.startswith('echo '):
                message = cmd[5:]
                # 
                message_id = endpoint.send('echo', {"message": message}, )
                print(f"已发送，ID: {message_id}")
            else:
                print("未知命令，使用'echo <消息>'发送消息")
                
    except KeyboardInterrupt:
        print("\n正在关闭...")