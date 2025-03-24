from netcore.endpoint  import Endpoint, Response, request
from netcore.blueprint import Blueprint
from netcore.lso import Pipe

# 创建管道和端点
pipe = Pipe(lambda size: b'', lambda data: None)
endpoint = Endpoint(pipe)

# 创建用户相关操作的蓝图
user_bp = Blueprint("users", "user")

@user_bp.request("list")
def user_list():
    # 注意使用的是与Endpoint.request相同的风格
    users = ["用户1", "用户2", "用户3"]
    return Response("user_list", {"users": users})

@user_bp.request("info")
def user_info():
    user_id = request.json.get("id", 0)
    return Response("user_info", {"id": user_id, "name": f"用户{user_id}"})

# 创建商品相关操作的蓝图
product_bp = Blueprint("products", "product")

@product_bp.request("list")
def product_list():
    products = ["商品1", "商品2", "商品3"]
    return Response("product_list", {"products": products})

# 注册蓝图到端点
endpoint.register_blueprint(user_bp).register_blueprint(product_bp)  # 支持链式调用

# 启动端点
endpoint.start() 