from contextvars import ContextVar
import logging
from typing import Any, List
from functools import wraps
from inspect import iscoroutine

log_contexts: List[str] = ContextVar('log_contexts', default=[])


class Log:
    '''
    A wrapper around Python's Logger class that adds a context description.
    '''

    def __init__(self, logger: logging.Logger) -> None:
        '''
        Initialize with the Logger to wrap.
        '''
        self.logger = logger

    def prefix(self) -> str:
        '''
        Build the prefix for the log message.

        This describes the context of the log message.
        '''

        context = log_contexts.get()
        return ' - '.join(context) + ': ' if len(context) else ''

    def debug(self, msg, *args, **kwargs) -> None:
        '''
        Log a debugging message.

        Use this for diagnosing programming issues.
        '''

        self.logger.debug(self.prefix() + msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs) -> None:
        '''
        Log an informational message.

        Use this for recording commands and their results.
        '''

        self.logger.info(self.prefix() + msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs) -> None:
        '''
        Log a warning message.

        Use this for recording permitted failures.
        '''

        self.logger.warning(self.prefix() + msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs) -> None:
        '''
        Log an error message.

        Use this for recording unexpected failures.
        '''

        self.logger.error(self.prefix() + msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs) -> None:
        '''
        Log a critical failure message.

        Use this when the application cannot continue and must exit.
        '''

        self.logger.critical(self.prefix() + msg, *args, **kwargs)


class LogContext:
    def __init__(self, name: str) -> None:
        self.name = name

    def __enter__(self) -> None:
        c = log_contexts.get()
        c.append(self.name)
        log_contexts.set(c)

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        c = log_contexts.get()
        c.pop()
        log_contexts.set(c)


def log_context(func):
    if iscoroutine(func):
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            with LogContext(func.__name__):
                return await func(*args, **kwargs)
    else:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            with LogContext(func.__name__):
                return func(*args, **kwargs)

    return wrapper


log = Log(logging.getLogger('ai'))
