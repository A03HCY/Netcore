from .endpoint  import Endpoint, Request, Response, request
from .blueprint import Blueprint
from .cache     import Cache
from .event     import EventEmitter
from .scheduler import Scheduler
from .lso       import Pipe, LsoProtocol, Utils

__version__ = '0.1.1'

__all__ = [
    'Endpoint',
    'Request',
    'Response',
    'request',
    'Blueprint',
    'Cache',
    'EventEmitter',
    'Scheduler',
    'Pipe',
    'LsoProtocol',
    'Utils',
    '__version__'
]

# 配置日志
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('netcore')