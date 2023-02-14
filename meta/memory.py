"""
This module defines decorators that allow function to keep track of known parameters.
"""

from typing import Callable, ParamSpec, TypeVar





P = ParamSpec("P")
T = TypeVar("T")

def cached(func : Callable[P, T]) -> Callable[P, T]:

    from functools import wraps
    from weakref import WeakKeyDictionary

    cache = WeakKeyDictionary()

    @wraps(func)
    def wrapped(*args, **kwargs):
        arg_vec = (args, tuple((k, v) for k, v in sorted(kwargs.items(), key=lambda x : x[0])))
        if arg_vec in cache:
            return cache[arg_vec]
        else:
            res = func(*args, **kwargs)
            cache[arg_vec] = res
            return res

    return wrapped