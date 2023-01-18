"""
This module adds a few useful class decorators to Python.
"""

from typing import Callable, Type, TypeVar, ParamSpec

__all__ = ["semistaticmethod"]





R = TypeVar("R")
P = ParamSpec("P")
T = TypeVar("T")

class semistaticmethod:

    """
    This decorator makes a function behave like a method when called on a class instance, but when called on the class, the "self" argument will be None.
    """

    def __init__(self, func : Callable[P, R]) -> None:
        self.__func__ = func
    
    def __get__(self, obj : T | None, cls : Type[T]) -> Callable[P, R]:
        from functools import wraps

        @wraps(self.__func__)
        def hybrid(*args, **kwargs):
            return self.__func__(obj, *args, **kwargs)

        hybrid.__func__ = hybrid.im_func = self.__func__
        hybrid.__self__ = hybrid.im_self = obj

        return hybrid
    

del Callable, Type, TypeVar, ParamSpec, R, P, T