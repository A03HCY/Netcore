from netcore.endpoint import Endpoint, Response, request
from netcore.blueprint import Blueprint
from netcore.lso import Pipe
import json
import time
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG)

# 创建管道和端点
pipe = Pipe(lambda size: b'', lambda data: None)
endpoint = Endpoint(pipe)

# 全局中间件 - 日志记录
@endpoint.middleware
def global_logger_middleware(handler):
    def wrapper():
        print(f"全局中间件: 处理路由请求")
        result = handler()
        print(f"全局中间件: 请求处理完成")
        return result
    return wrapper

# 全局错误处理
@endpoint.error_handle
def global_error_handler(error):
    print(f"全局错误处理: {str(error)}")
    return Response("error", {
        "error": str(error),
        "handled_by": "global"
    })

# 请求前钩子
@endpoint.before_request
def global_before_request():
    print(f"全局请求前: {request.string[:50]}...")

# 请求后钩子
@endpoint.after_request
def global_after_request(response):
    print(f"全局请求后: 响应路由 {response.route}")
    return response

# 创建用户API蓝图
user_bp = Blueprint("users", "user")

# 蓝图中间件 - 认证
@user_bp.middleware
def auth_middleware(handler):
    def wrapper():
        token = request.json.get("token")
        if not token or token != "valid_token":
            return Response("user_error", {"error": "未授权访问"})
        return handler()
    return wrapper

# 蓝图错误处理
@user_bp.error_handle
def user_error_handler(error):
    return Response("user_error", {
        "error": str(error),
        "handled_by": "user_blueprint"
    })

# 蓝图路由
@user_bp.request("list")
def user_list():
    users = ["用户1", "用户2", "用户3"]
    return Response("user_list", {"users": users})

@user_bp.request("info")
def user_info():
    user_id = request.json.get("id", 0)
    if user_id <= 0:
        raise ValueError("无效的用户ID")
    return Response("user_info", {"id": user_id, "name": f"用户{user_id}"})

# 全局路由
@endpoint.request("status")
def system_status():
    return Response("status", {"status": "运行中"})

# 注册蓝图到端点
endpoint.register_blueprint(user_bp)

# 启动端点
endpoint.start() 