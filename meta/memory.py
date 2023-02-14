"""
This module defines decorators that allow function to keep track of known parameters.
"""

from typing import Callable, ParamSpec, TypeVar





class ArgumentVector:

    """
    This class is internally used to store arguments given to functions no matter their signature.
    """

    __existing : set["ArgumentVector"] = set()

    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs
        self.__hash = None

        try:
            hash(self)
        except:
            raise TypeError("ArgumentVector object can only use hashable arguments")
        
        from weakref import finalize, ref

        ArgumentVector.__existing.add(self)
        finalizers : list[finalize] = []

        def finalizer():
            ArgumentVector.__existing.discard(self)
            for fin in finalizers:
                fin.detach()
            finalizers.clear()
        
        def simple_ref(obj : object):
            return lambda : obj
        
        self.args = []
        for e in args:
            try:
                finalizers.append(finalize(e, finalizer))
                self.args.append(ref(e))
            except TypeError:
                self.args.append(simple_ref(e))
        self.args = tuple(self.args)

        self.kwargs = {}
        for k, v in kwargs.items():
            try:
                finalizers.append(finalize(v, finalizer))
                self.kwargs[k] = ref(v)
            except TypeError:
                self.kwargs[k] = simple_ref(v)
    
    def __eq__(self, o: object) -> bool:
        if not isinstance(o, ArgumentVector):
            return False
        if self is o:
            return True
        return [e() for e in self.args] == [e() for e in o.args] and {k : v() for k, v in self.kwargs.items()} == {k : v() for k, v in o.kwargs.items()}
    
    def __hash__(self) -> int:
        if self.__hash != None:
            return self.__hash
        else:
            self.__hash = hash(hash(self.args) + hash([(k, v) for k, v in sorted(self.kwargs.items(), key=lambda x : x[0])]))
            return self.__hash





P = ParamSpec("P")
T = TypeVar("T")

def cached(func : Callable[P, T]) -> Callable[P, T]:
    
    """
    Creates a cached version of the function.
    Each call to the function will be recorded with the given parameters, and subsequent calls with the same parameters will be skipped and the cached value will be directly returned.
    Note that functions must be true function for this to be meaningful (not recommended if a function might give different results with the same inputs).
    Also, if any of the arguments are not hashable, cache will be ignored.
    """

    from functools import wraps
    from weakref import WeakKeyDictionary
    from typing import Any

    cache : WeakKeyDictionary[ArgumentVector, Any] = WeakKeyDictionary()

    @wraps(func)
    def wrapped(*args, **kwargs):
        try:
            arg_vec = ArgumentVector(*args, **kwargs)
        except:
            arg_vec = None
        if arg_vec and arg_vec in cache:
            return cache[arg_vec]
        else:
            res = func(*args, **kwargs)
            if arg_vec:
                cache[arg_vec] = res
            return res

    return wrapped