"""
This module is used to run all tests that Viper must pass before a distribution is made.
"""

import logging
from logging import LogRecord
from sys import stderr, stdout
from threading import RLock

__all__ = ["run_all", "logger", "set_level", "debug", "info", "warning", "exception", "error", "critical", "fatal", "log", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]





def run_all():
    """
    Runs all the available tests.
    """

    from pathlib import Path
    from importlib import import_module
    from itertools import chain

    for p in chain(Path(__file__).parent.glob("*.py"), (p for p in Path(__file__).parent.iterdir() if p.is_dir() and (p / "__init__.py").is_file())):
        if p.name not in ("__init__.py", "__main__.py"):
            import_module(f".{p.stem}", __package__)





logger = logging.Logger("Boa.parallel Logger")
error_handler = logging.StreamHandler(stderr)
error_handler.formatter = logging.Formatter("\033[91m%(levelname)-8s\033[0m : \033[94m%(module)-11s\033[0m : %(asctime)-23s : \033[91m%(message)s\033[0m")
warning_handler = logging.StreamHandler(stderr)
warning_handler.formatter = logging.Formatter("\033[93m%(levelname)-8s\033[0m : \033[94m%(module)-11s\033[0m : %(asctime)-23s : \033[93m%(message)s\033[0m")
normal_handler = logging.StreamHandler(stdout)
normal_handler.formatter = logging.Formatter("\033[92m%(levelname)-8s\033[0m : \033[94m%(module)-11s\033[0m : %(asctime)-23s : %(message)s")
logger.addHandler(error_handler)
logger.addHandler(warning_handler)
logger.addHandler(normal_handler)





class RangeFilter(logging.Filter):

    """
    Subclass of filters which allow to filter logs with a level in between two integers.
    """

    def __init__(self, name: str = "") -> None:
        import logging
        super().__init__(name)
        self.__min = 0
        self.__max = logging.CRITICAL

    @property
    def min(self) -> int:
        """
        The lowest level an accepted log can have (included).
        """
        return self.__min
    
    @min.setter
    def min(self, value : int):
        if not isinstance(value, int):
            raise TypeError(f"Expected int, got '{type(value).__name__}'")
        self.__min = value

    @property
    def max(self) -> int:
        """
        The highest level an accepted log can have (excluded).
        """
        return self.__max
    
    @max.setter
    def max(self, value : int):
        if not isinstance(value, int):
            raise TypeError(f"Expected int, got '{type(value).__name__}'")
        self.__max = value
    
    def filter(self, record: LogRecord) -> bool:
        return record.levelno in range(self.min, self.max) and super().filter(record)
    




normal_filter = RangeFilter()
normal_handler.addFilter(normal_filter)
warning_filter = RangeFilter()
warning_handler.addFilter(warning_filter)

def set_level(n : int):
    """
    Sets the level of logging.
    """
    from logging import WARNING, ERROR
    normal_filter.min = min(n, WARNING)
    normal_filter.max = WARNING
    warning_filter.min = min(max(n, WARNING), ERROR)
    warning_filter.max = ERROR
    error_handler.setLevel(max(ERROR, n))

set_level(logging.WARNING)
lock = RLock()

def debug(msg : str, *args, exc_info = None, stack_info : bool = False, stacklevel : int = 1, extra : dict[str, object] | None = None):
    with lock:
        logger.debug(msg, *args, exc_info=exc_info, stack_info=stack_info, stacklevel=stacklevel + 1, extra=extra)
        normal_handler.flush()

def info(msg : str, *args, exc_info = None, stack_info : bool = False, stacklevel : int = 1, extra : dict[str, object] | None = None):
    with lock:
        logger.info(msg, *args, exc_info=exc_info, stack_info=stack_info, stacklevel=stacklevel + 1, extra=extra)
        normal_handler.flush()

def warning(msg : str, *args, exc_info = None, stack_info : bool = False, stacklevel : int = 1, extra : dict[str, object] | None = None):
    with lock:
        logger.warning(msg, *args, exc_info=exc_info, stack_info=stack_info, stacklevel=stacklevel + 1, extra=extra)
        warning_handler.flush()

def exception(msg : str, *args, exc_info = None, stack_info : bool = False, stacklevel : int = 1, extra : dict[str, object] | None = None):
    with lock:
        logger.exception(msg, *args, exc_info=exc_info, stack_info=stack_info, stacklevel=stacklevel + 1, extra=extra)
        error_handler.flush()

def error(msg : str, *args, exc_info = None, stack_info : bool = False, stacklevel : int = 1, extra : dict[str, object] | None = None):
    with lock:
        logger.error(msg, *args, exc_info=exc_info, stack_info=stack_info, stacklevel=stacklevel + 1, extra=extra)
        error_handler.flush()

def critical(msg : str, *args, exc_info = None, stack_info : bool = False, stacklevel : int = 1, extra : dict[str, object] | None = None):
    with lock:
        logger.critical(msg, *args, exc_info=exc_info, stack_info=stack_info, stacklevel=stacklevel + 1, extra=extra)
        error_handler.flush()

def fatal(msg : str, *args, exc_info = None, stack_info : bool = False, stacklevel : int = 1, extra : dict[str, object] | None = None):
    with lock:
        logger.fatal(msg, *args, exc_info=exc_info, stack_info=stack_info, stacklevel=stacklevel + 1, extra=extra)
        error_handler.flush()

def log(level : int, msg : str, *args, exc_info = None, stack_info : bool = False, stacklevel : int = 1, extra : dict[str, object] | None = None):
    with lock:
        logger.log(level, msg, *args, exc_info=exc_info, stack_info=stack_info, stacklevel=stacklevel + 1, extra=extra)
        error_handler.flush()

DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL





del logging, stderr, stdout, LogRecord, RangeFilter, RLock