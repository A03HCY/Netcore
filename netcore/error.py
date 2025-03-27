from typing import Any

import datetime



class NetcoreError(Exception):
    """Base exception for all network-related errors."""
    def __init__(self, message: str, original: Exception = None):
        super().__init__(message)
        self.original_error = original
        self.timestamp = datetime.datetime.now()


class NetcorePipeError(NetcoreError):...


class EndpointError(NetcoreError):...


class EndpointHandleError(EndpointError):...


class EndpointMiddlewareError(EndpointError):...


class EndpointRouteError(EndpointError):...


class EndpointRouteNotFound(EndpointRouteError):...