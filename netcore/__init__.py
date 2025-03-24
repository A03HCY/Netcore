import logging

# 创建日志处理器
logger = logging.getLogger("netcore")
logger.setLevel(logging.WARNING)  # 默认只显示警告和错误

# 设置默认处理器
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# 导出版本信息
__version__ = "0.1.1"
